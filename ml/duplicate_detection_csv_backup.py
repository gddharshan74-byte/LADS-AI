import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path


DATA_PATH = "backend/data/mplads_demo_expanded.csv"

OUTPUT_PAIRS = "backend/data/duplicate_results.csv"
OUTPUT_PROJECTS = "backend/data/duplicate_project_signals.csv"

# Prototype threshold.
# This is NOT an official MPLADS threshold.
SIMILARITY_THRESHOLD = 0.80


def detect_similar_projects(df: pd.DataFrame) -> list:
    """
    Compare project descriptions using TF-IDF and cosine similarity.

    Projects are compared within the same category.

    Returns a list of potentially similar project pairs.
    """

    results = []

    for category, group in df.groupby("category"):
        group = group.reset_index(drop=True)

        if len(group) < 2:
            continue

        descriptions = (
            group["work_description"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
        )

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        tfidf_matrix = vectorizer.fit_transform(descriptions)

        similarity_matrix = cosine_similarity(tfidf_matrix)

        for i in range(len(group)):
            for j in range(i + 1, len(group)):

                similarity_score = similarity_matrix[i, j]

                if similarity_score >= SIMILARITY_THRESHOLD:

                    results.append(
                        {
                            "project_1": group.loc[i, "project_id"],
                            "project_2": group.loc[j, "project_id"],
                            "category": category,
                            "similarity_pct": round(
                                similarity_score * 100, 2
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
        reverse=True
    )

    return results


def create_project_signals(results: list) -> pd.DataFrame:
    """
    Convert pair-level similarity results into a project-level
    duplicate/overlap signal.

    Each project gets its strongest similarity score and the
    number of potentially similar projects.
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
                project_scores[project_1]["max_similarity_pct"],
                similarity
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
                project_scores[project_2]["max_similarity_pct"],
                similarity
            )

            project_scores[project_2][
                "similar_project_count"
            ] += 1

    return pd.DataFrame(project_scores.values())


def main():

    print("\nLADS AI — DUPLICATE WORK DETECTION")
    print("=" * 75)

    # Load dataset
    df = pd.read_csv(DATA_PATH)

    print(f"Projects analyzed: {len(df)}")
    print(
        f"Similarity threshold: "
        f"{SIMILARITY_THRESHOLD * 100:.0f}%"
    )

    # Detect similar pairs
    results = detect_similar_projects(df)

    print("\nPotentially Similar Works")
    print("=" * 75)

    if not results:

        print("No potentially similar works detected.")

    else:

        # Display top 20 results
        for result in results[:20]:

            print(
                f"\n{result['project_1']} "
                f"↔ {result['project_2']}"
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

    # ---------------------------------------------------------
    # Save pair-level results
    # ---------------------------------------------------------

    output_folder = Path("backend/data")
    output_folder.mkdir(
        parents=True,
        exist_ok=True
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
        index=False
    )

    # ---------------------------------------------------------
    # Save project-level duplicate signals
    # ---------------------------------------------------------

    project_signals = create_project_signals(results)

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
        index=False
    )

    print("\nOutput files created")
    print("=" * 75)

    print(
        f"Pair results: "
        f"{OUTPUT_PAIRS}"
    )

    print(
        f"Project signals: "
        f"{OUTPUT_PROJECTS}"
    )


if __name__ == "__main__":
    main()