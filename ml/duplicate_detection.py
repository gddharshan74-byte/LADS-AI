import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from database import SessionLocal
from models.database_models import Project
from ml.db_writer import save_duplicate_results


# ============================================================
# OUTPUT PATHS
# ============================================================

OUTPUT_PAIRS = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "duplicate_results.csv"
)

OUTPUT_PROJECTS = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "duplicate_project_signals.csv"
)


# ============================================================
# PROTOTYPE THRESHOLD
# ============================================================

# This is a prototype threshold.
# It is NOT an official MPLADS threshold.
SIMILARITY_THRESHOLD = 0.80


# ============================================================
# LOAD PROJECTS FROM POSTGRESQL
# ============================================================

def load_projects_from_database() -> pd.DataFrame:
    """
    Load the project records required for similarity analysis
    directly from PostgreSQL.
    """

    db = SessionLocal()

    try:
        rows = (
            db.query(
                Project.project_id,
                Project.category,
                Project.work_description,
            )
            .order_by(Project.project_id)
            .all()
        )

        records = [
            {
                "project_id": row.project_id,
                "category": row.category,
                "work_description": row.work_description,
            }
            for row in rows
        ]

        return pd.DataFrame(records)

    finally:
        db.close()


# ============================================================
# DETECT SIMILAR PROJECTS
# ============================================================

def detect_similar_projects(df: pd.DataFrame) -> list:
    """
    Compare project descriptions using TF-IDF and cosine similarity.

    Projects are compared within the same category.

    Returns a list of potentially similar project pairs.
    """

    required_columns = [
        "project_id",
        "category",
        "work_description",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Project data is missing columns: {missing_columns}"
        )

    results = []

    working_df = df.copy()

    working_df["category"] = (
        working_df["category"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    working_df["work_description"] = (
        working_df["work_description"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    for category, group in working_df.groupby("category"):

        group = group.reset_index(drop=True)

        if len(group) < 2:
            continue

        descriptions = group["work_description"]

        # Skip groups where every description is empty.
        if not descriptions.str.strip().any():
            continue

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
        )

        tfidf_matrix = vectorizer.fit_transform(
            descriptions
        )

        similarity_matrix = cosine_similarity(
            tfidf_matrix
        )

        for i in range(len(group)):

            for j in range(i + 1, len(group)):

                similarity_score = similarity_matrix[i, j]

                if similarity_score >= SIMILARITY_THRESHOLD:

                    results.append(
                        {
                            "project_1": group.loc[
                                i, "project_id"
                            ],
                            "project_2": group.loc[
                                j, "project_id"
                            ],
                            "category": category,
                            "similarity_pct": round(
                                similarity_score * 100,
                                2,
                            ),
                            "description_1": group.loc[
                                i, "work_description"
                            ],
                            "description_2": group.loc[
                                j, "work_description"
                            ],
                        }
                    )

    results.sort(
        key=lambda x: x["similarity_pct"],
        reverse=True,
    )

    return results


# ============================================================
# CREATE PROJECT-LEVEL SIGNALS
# ============================================================

def create_project_signals(
    results: list,
) -> pd.DataFrame:
    """
    Convert pair-level similarity results into a project-level
    duplicate/overlap signal.

    Each project receives its strongest similarity score and
    the number of potentially similar projects.
    """

    project_scores = {}

    for result in results:

        project_1 = result["project_1"]
        project_2 = result["project_2"]
        similarity = result["similarity_pct"]

        if project_1 not in project_scores:

            project_scores[project_1] = {
                "project_id": project_1,
                "max_similarity_pct": similarity,
                "similar_project_count": 1,
                "duplicate_signal": True,
            }

        else:

            project_scores[project_1][
                "max_similarity_pct"
            ] = max(
                project_scores[project_1][
                    "max_similarity_pct"
                ],
                similarity,
            )

            project_scores[project_1][
                "similar_project_count"
            ] += 1

        if project_2 not in project_scores:

            project_scores[project_2] = {
                "project_id": project_2,
                "max_similarity_pct": similarity,
                "similar_project_count": 1,
                "duplicate_signal": True,
            }

        else:

            project_scores[project_2][
                "max_similarity_pct"
            ] = max(
                project_scores[project_2][
                    "max_similarity_pct"
                ],
                similarity,
            )

            project_scores[project_2][
                "similar_project_count"
            ] += 1

    return pd.DataFrame(
        project_scores.values()
    )


# ============================================================
# SAVE CSV BACKUPS
# ============================================================

def save_csv_backups(
    results: list,
    project_signals: pd.DataFrame,
):
    """
    Keep CSV outputs as backups while PostgreSQL is the
    primary storage for project-level duplicate signals.
    """

    OUTPUT_PAIRS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pair_df = pd.DataFrame(results)

    if pair_df.empty:

        pair_df = pd.DataFrame(
            columns=[
                "project_1",
                "project_2",
                "category",
                "similarity_pct",
                "description_1",
                "description_2",
            ]
        )

    pair_df.to_csv(
        OUTPUT_PAIRS,
        index=False,
    )

    if project_signals.empty:

        project_signals = pd.DataFrame(
            columns=[
                "project_id",
                "max_similarity_pct",
                "similar_project_count",
                "duplicate_signal",
            ]
        )

    project_signals.to_csv(
        OUTPUT_PROJECTS,
        index=False,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nPRISM AI — NLP SIMILARITY DETECTION")
    print("=" * 75)

    # --------------------------------------------------------
    # Load projects from PostgreSQL
    # --------------------------------------------------------

    try:

        df = load_projects_from_database()

    except Exception as error:

        print("\nERROR while loading projects from PostgreSQL.")
        print(error)
        return

    print(
        f"Projects loaded from PostgreSQL: {len(df)}"
    )

    print(
        f"Similarity threshold: "
        f"{SIMILARITY_THRESHOLD * 100:.0f}%"
    )

    if df.empty:

        print(
            "\nNo projects were found in the PostgreSQL database."
        )
        return

    # --------------------------------------------------------
    # Detect similar project pairs
    # --------------------------------------------------------

    try:

        results = detect_similar_projects(df)

    except Exception as error:

        print(
            "\nERROR during NLP similarity analysis."
        )
        print(error)
        return

    print("\nPotentially Similar Works")
    print("=" * 75)

    if not results:

        print(
            "No potentially similar works detected."
        )

    else:

        for result in results[:20]:

            print(
                f"\n{result['project_1']} "
                f"<-> {result['project_2']}"
            )

            print(
                f"Category: {result['category']}"
            )

            print(
                f"Similarity: "
                f"{result['similarity_pct']:.1f}%"
            )

            print(
                f"Project 1: "
                f"{result['description_1']}"
            )

            print(
                f"Project 2: "
                f"{result['description_2']}"
            )

            print("-" * 75)

    print(
        f"\nTotal potentially similar pairs found: "
        f"{len(results)}"
    )

    # --------------------------------------------------------
    # Create project-level signals
    # --------------------------------------------------------

    project_signals = create_project_signals(
        results
    )

    if project_signals.empty:

        project_signals = pd.DataFrame(
            columns=[
                "project_id",
                "max_similarity_pct",
                "similar_project_count",
                "duplicate_signal",
            ]
        )

    # --------------------------------------------------------
    # Save CSV backups
    # --------------------------------------------------------

    save_csv_backups(
        results,
        project_signals,
    )

    # --------------------------------------------------------
    # Write project-level signals to PostgreSQL
    # --------------------------------------------------------

    try:

        written_count = save_duplicate_results(
            project_signals
        )

        print("\nDatabase Storage")
        print("=" * 75)

        print(
            f"Duplicate signals written to PostgreSQL: "
            f"{written_count}"
        )

    except Exception as error:

        print(
            "\nERROR while writing duplicate signals "
            "to PostgreSQL."
        )

        print(error)
        return

    # --------------------------------------------------------
    # Output summary
    # --------------------------------------------------------

    print("\nBackup files created")
    print("=" * 75)

    print(
        f"Pair results: {OUTPUT_PAIRS}"
    )

    print(
        f"Project signals backup: {OUTPUT_PROJECTS}"
    )

    print(
        "\nPRISM AI NLP similarity detection "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
