import pandas as pd
from pathlib import Path


# ============================================================
# FILE PATHS
# ============================================================

DATA_PATH = "backend/data/mplads_demo_expanded.csv"
DUPLICATE_PATH = "backend/data/duplicate_project_signals.csv"
SPENDING_PATH = "backend/data/spending_results.csv"
OUTPUT_PATH = "backend/data/project_risk_results.csv"


# ============================================================
# RISK SCORE WEIGHTS
# ============================================================

# These are prototype design weights.
# They are NOT official MPLADS/government thresholds.

COST_WEIGHT = 30
DELAY_WEIGHT = 30
DUPLICATE_WEIGHT = 20
SPENDING_WEIGHT = 20


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """
    Load:
    1. Main MPLADS project dataset
    2. NLP duplicate/overlap signals
    3. Spending-pattern analysis results
    """

    projects = pd.read_csv(DATA_PATH)

    duplicate_signals = pd.read_csv(DUPLICATE_PATH)

    spending_results = pd.read_csv(SPENDING_PATH)

    return projects, duplicate_signals, spending_results


# ============================================================
# COST SCORE
# ============================================================

def calculate_cost_score(row):
    """
    Convert expenditure overrun relative to sanctioned amount
    into a score from 0 to 30.

    0% or less overrun  -> 0 points
    60% or more         -> 30 points

    This is a prototype scoring scale.
    """

    overrun = row["sanction_overrun_pct"]

    if pd.isna(overrun) or overrun <= 0:
        return 0

    if overrun >= 60:
        return COST_WEIGHT

    score = (overrun / 60) * COST_WEIGHT

    return round(score, 2)


# ============================================================
# DELAY SCORE
# ============================================================

def calculate_delay_score(row):
    """
    Convert project delay percentage into a score from 0 to 30.

    0% delay or less -> 0 points
    60% or more      -> 30 points
    """

    delay = row["delay_pct"]

    if pd.isna(delay) or delay <= 0:
        return 0

    if delay >= 60:
        return DELAY_WEIGHT

    score = (delay / 60) * DELAY_WEIGHT

    return round(score, 2)


# ============================================================
# DUPLICATE / OVERLAP SCORE
# ============================================================

def calculate_duplicate_score(row):
    """
    Convert NLP similarity into a score from 0 to 20.

    Less than 80% similarity -> 0
    80% similarity            -> 0
    100% similarity           -> 20

    The similarity threshold is a prototype setting,
    not an official MPLADS rule.
    """

    similarity = row.get("max_similarity_pct", 0)

    if pd.isna(similarity):
        similarity = 0

    if similarity < 80:
        return 0

    if similarity >= 100:
        return DUPLICATE_WEIGHT

    score = (
        (similarity - 80) / 20
    ) * DUPLICATE_WEIGHT

    return round(score, 2)


# ============================================================
# SPENDING PATTERN SCORE
# ============================================================

def calculate_spending_score(row):
    """
    Convert category-relative spending unusualness into
    a score from 0 to 20.

    The spending signal is based on a category-level
    z-score rather than simply repeating cost overrun.
    """

    zscore = row.get("spending_zscore", 0)

    if pd.isna(zscore) or zscore <= 0:
        return 0

    if zscore >= 4:
        return SPENDING_WEIGHT

    score = (
        zscore / 4
    ) * SPENDING_WEIGHT

    return round(score, 2)


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(score):
    """
    Convert the final risk score into a simple category.

    0  - 39.99 -> Low
    40 - 69.99 -> Medium
    70 - 100   -> High
    """

    if score >= 70:
        return "High"

    if score >= 40:
        return "Medium"

    return "Low"


# ============================================================
# EXPLAINABLE REASONS
# ============================================================

def build_risk_reasons(row):
    """
    Generate human-readable reasons explaining why
    a project received its risk score.
    """

    reasons = []

    # Cost
    if row["cost_score"] > 0:
        reasons.append(
            f"Cost overrun of "
            f"{row['sanction_overrun_pct']:.1f}% "
            f"above sanctioned amount"
        )

    # Delay
    if row["delay_score"] > 0:
        reasons.append(
            f"Project duration exceeds plan by "
            f"{row['delay_pct']:.1f}%"
        )

    # Duplicate / similarity
    if row["duplicate_score"] > 0:
        reasons.append(
            f"Similar work description detected "
            f"({row['max_similarity_pct']:.1f}% similarity)"
        )

    # Spending pattern
    if row["spending_score"] > 0:
        reasons.append(
            f"Expenditure is unusually high for the "
            f"{row['category']} category "
            f"(z-score: {row['spending_zscore']:.2f})"
        )

    # No significant signal
    if not reasons:
        reasons.append(
            "No major anomaly signals detected"
        )

    return " | ".join(reasons)


# ============================================================
# BUILD RISK ENGINE
# ============================================================

def build_risk_engine():
    """
    Build the complete project-level LADS AI risk dataset.
    """

    projects, duplicate_signals, spending_results = load_data()

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    required_project_columns = [
        "project_id",
        "category",
        "estimated_cost_lakh",
        "sanctioned_amount_lakh",
        "expenditure_lakh",
        "planned_duration_days",
        "elapsed_days",
        "current_status",
    ]

    missing_columns = [
        column
        for column in required_project_columns
        if column not in projects.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Main dataset is missing columns: {missing_columns}"
        )

    # ========================================================
    # COST SIGNAL
    # ========================================================

    projects["sanction_overrun_pct"] = (
        (
            projects["expenditure_lakh"]
            - projects["sanctioned_amount_lakh"]
        )
        / projects["sanctioned_amount_lakh"]
    ) * 100

    # ========================================================
    # DELAY SIGNAL
    # ========================================================

    projects["delay_days"] = (
        projects["elapsed_days"]
        - projects["planned_duration_days"]
    )

    projects["delay_pct"] = (
        projects["delay_days"]
        / projects["planned_duration_days"]
    ) * 100

    # ========================================================
    # MERGE NLP DUPLICATE SIGNAL
    # ========================================================

    duplicate_columns = [
        "project_id",
        "max_similarity_pct",
        "similar_project_count",
        "duplicate_signal",
    ]

    missing_duplicate_columns = [
        column
        for column in duplicate_columns
        if column not in duplicate_signals.columns
    ]

    if missing_duplicate_columns:
        raise ValueError(
            "Duplicate results are missing columns: "
            f"{missing_duplicate_columns}"
        )

    duplicate_signals = duplicate_signals[
        duplicate_columns
    ].copy()

    projects = projects.merge(
        duplicate_signals,
        on="project_id",
        how="left"
    )

    projects["max_similarity_pct"] = (
        projects["max_similarity_pct"]
        .fillna(0)
    )

    projects["similar_project_count"] = (
        projects["similar_project_count"]
        .fillna(0)
    )

    projects["duplicate_signal"] = (
        projects["duplicate_signal"]
        .fillna(False)
    )

    # ========================================================
    # MERGE SPENDING ANALYSIS
    # ========================================================

    spending_columns = [
        "project_id",
        "category_avg_expenditure_lakh",
        "category_std_expenditure_lakh",
        "spending_zscore",
        "spending_anomaly",
    ]

    missing_spending_columns = [
        column
        for column in spending_columns
        if column not in spending_results.columns
    ]

    if missing_spending_columns:
        raise ValueError(
            "Spending results are missing columns: "
            f"{missing_spending_columns}"
        )

    spending_results = spending_results[
        spending_columns
    ].copy()

    projects = projects.merge(
        spending_results,
        on="project_id",
        how="left"
    )

    projects["spending_zscore"] = (
        projects["spending_zscore"]
        .fillna(0)
    )

    projects["spending_anomaly"] = (
        projects["spending_anomaly"]
        .fillna(False)
    )

    # ========================================================
    # COMPONENT SCORES
    # ========================================================

    projects["cost_score"] = projects.apply(
        calculate_cost_score,
        axis=1
    )

    projects["delay_score"] = projects.apply(
        calculate_delay_score,
        axis=1
    )

    projects["duplicate_score"] = projects.apply(
        calculate_duplicate_score,
        axis=1
    )

    projects["spending_score"] = projects.apply(
        calculate_spending_score,
        axis=1
    )

    # ========================================================
    # FINAL RISK SCORE
    # ========================================================

    projects["risk_score"] = (
        projects["cost_score"]
        + projects["delay_score"]
        + projects["duplicate_score"]
        + projects["spending_score"]
    ).round(2)

    # Keep the score inside 0-100.
    projects["risk_score"] = (
        projects["risk_score"]
        .clip(lower=0, upper=100)
    )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    projects["risk_level"] = projects[
        "risk_score"
    ].apply(get_risk_level)

    # ========================================================
    # EXPLANATIONS
    # ========================================================

    projects["risk_reasons"] = projects.apply(
        build_risk_reasons,
        axis=1
    )

    return projects


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 80)
    print("              LADS AI — RISK INTELLIGENCE ENGINE")
    print("=" * 80)

    try:

        results = build_risk_engine()

    except FileNotFoundError as error:

        print("\nERROR: Required file not found.")
        print(error)
        return

    except ValueError as error:

        print("\nERROR: Dataset structure problem.")
        print(error)
        return

    except Exception as error:

        print("\nERROR while building the Risk Engine.")
        print(error)
        return

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    output_folder = Path("backend/data")

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    results.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        f"\nProjects analyzed: {len(results)}"
    )

    print("\nRisk Distribution")
    print("=" * 80)

    risk_distribution = (
        results["risk_level"]
        .value_counts()
        .reindex(
            ["High", "Medium", "Low"],
            fill_value=0
        )
    )

    print(
        risk_distribution.to_string()
    )

    # ========================================================
    # TOP PRIORITY PROJECTS
    # ========================================================

    top_projects = (
        results
        .sort_values(
            "risk_score",
            ascending=False
        )
        .head(10)
    )

    print("\nTop 10 Priority Projects")
    print("=" * 80)

    display_columns = [
        "project_id",
        "category",
        "risk_score",
        "risk_level",
        "risk_reasons",
    ]

    print(
        top_projects[
            display_columns
        ].to_string(
            index=False
        )
    )

    # ========================================================
    # SCORE COMPONENT SUMMARY
    # ========================================================

    print("\nRisk Score Components")
    print("=" * 80)

    print(
        f"Maximum Cost Score      : {COST_WEIGHT}"
    )

    print(
        f"Maximum Delay Score     : {DELAY_WEIGHT}"
    )

    print(
        f"Maximum Duplicate Score : {DUPLICATE_WEIGHT}"
    )

    print(
        f"Maximum Spending Score  : {SPENDING_WEIGHT}"
    )

    print(
        f"Maximum Total Score     : "
        f"{COST_WEIGHT + DELAY_WEIGHT + DUPLICATE_WEIGHT + SPENDING_WEIGHT}"
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print("\nOutput file created:")
    print(OUTPUT_PATH)

    print("\nRisk engine completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()