import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer


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

# Prototype design weights.
# These are NOT official MPLADS/government thresholds.

COST_WEIGHT = 30
DELAY_WEIGHT = 30
DUPLICATE_WEIGHT = 20
SPENDING_WEIGHT = 20


# ============================================================
# PROTOTYPE SCORING THRESHOLDS
# ============================================================

# Cost:
# 0% or less      -> 0
# 60% or more     -> maximum score

COST_FULL_SCORE_AT = 60.0


# Delay:
# 0% or less      -> 0
# 60% or more     -> maximum score

DELAY_FULL_SCORE_AT = 60.0


# Similarity:
# < 80%           -> 0
# 100%             -> maximum score

DUPLICATE_MIN_SIMILARITY = 80.0
DUPLICATE_FULL_SCORE_AT = 100.0


# Spending:
# z <= 1.0        -> 0
# z >= 4.0        -> maximum score

SPENDING_MIN_ZSCORE = 1.0
SPENDING_FULL_SCORE_AT = 4.0


# ============================================================
# ISOLATION FOREST CONFIGURATION
# ============================================================

# Isolation Forest is used as an additional unsupervised
# anomaly signal.
#
# IMPORTANT:
# - It does NOT determine fraud.
# - It does NOT replace the explainable risk score.
# - It provides an additional anomaly signal for review.

ISOLATION_CONTAMINATION = 0.05
ISOLATION_RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """
    Load:
        1. Main MPLADS-like project dataset
        2. NLP duplicate/overlap signals
        3. Spending-pattern analysis results
    """

    projects = pd.read_csv(DATA_PATH)

    duplicate_signals = pd.read_csv(
        DUPLICATE_PATH
    )

    spending_results = pd.read_csv(
        SPENDING_PATH
    )

    return (
        projects,
        duplicate_signals,
        spending_results,
    )


# ============================================================
# SAFE NUMERIC HELPER
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        if pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


# ============================================================
# COST SCORE
# ============================================================

def calculate_cost_score(row):
    """
    Convert expenditure overrun relative to sanctioned amount
    into a score from 0 to 30.

    0% or less overrun -> 0 points
    60% or more        -> 30 points

    This is a prototype scoring scale.
    """

    overrun = safe_float(
        row.get("sanction_overrun_pct"),
        0.0,
    )

    if overrun <= 0:
        return 0.0

    if overrun >= COST_FULL_SCORE_AT:
        return float(COST_WEIGHT)

    score = (
        overrun / COST_FULL_SCORE_AT
    ) * COST_WEIGHT

    return round(score, 2)


# ============================================================
# DELAY SCORE
# ============================================================

def calculate_delay_score(row):
    """
    Convert project delay percentage into a score from 0 to 30.

    0% delay or less -> 0 points
    60% or more      -> 30 points

    This is a prototype scoring scale.
    """

    delay = safe_float(
        row.get("delay_pct"),
        0.0,
    )

    if delay <= 0:
        return 0.0

    if delay >= DELAY_FULL_SCORE_AT:
        return float(DELAY_WEIGHT)

    score = (
        delay / DELAY_FULL_SCORE_AT
    ) * DELAY_WEIGHT

    return round(score, 2)


# ============================================================
# DUPLICATE / OVERLAP SCORE
# ============================================================

def calculate_duplicate_score(row):
    """
    Convert NLP similarity into a score from 0 to 20.

    < 80% similarity -> 0
    80% similarity   -> starts contributing
    100% similarity  -> 20 points

    This is a prototype setting, not an official MPLADS rule.
    """

    similarity = safe_float(
        row.get("max_similarity_pct"),
        0.0,
    )

    if similarity < DUPLICATE_MIN_SIMILARITY:
        return 0.0

    if similarity >= DUPLICATE_FULL_SCORE_AT:
        return float(DUPLICATE_WEIGHT)

    score = (
        (
            similarity
            - DUPLICATE_MIN_SIMILARITY
        )
        / (
            DUPLICATE_FULL_SCORE_AT
            - DUPLICATE_MIN_SIMILARITY
        )
    ) * DUPLICATE_WEIGHT

    return round(score, 2)


# ============================================================
# SPENDING PATTERN SCORE
# ============================================================

def calculate_spending_score(row):
    """
    Convert category-relative spending unusualness into
    a score from 0 to 20.

    z-score <= 1.0 -> 0
    z-score >= 4.0 -> 20

    This prevents small deviations from the category
    baseline from creating unnecessary risk points.
    """

    zscore = safe_float(
        row.get("spending_zscore"),
        0.0,
    )

    if zscore <= SPENDING_MIN_ZSCORE:
        return 0.0

    if zscore >= SPENDING_FULL_SCORE_AT:
        return float(SPENDING_WEIGHT)

    score = (
        (
            zscore
            - SPENDING_MIN_ZSCORE
        )
        / (
            SPENDING_FULL_SCORE_AT
            - SPENDING_MIN_ZSCORE
        )
    ) * SPENDING_WEIGHT

    return round(score, 2)


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(score):
    """
    Convert the final risk score into a simple category.

    0 - 39.99  -> Low
    40 - 69.99 -> Medium
    70 - 100   -> High

    These are prototype thresholds.
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
    a project received its rule-based risk score.
    """

    reasons = []

    # --------------------------------------------------------
    # Cost
    # --------------------------------------------------------

    cost_score = safe_float(
        row.get("cost_score"),
        0.0,
    )

    cost_overrun = safe_float(
        row.get("sanction_overrun_pct"),
        0.0,
    )

    if cost_score > 0:

        if cost_overrun >= 60:
            reasons.append(
                f"High cost overrun of "
                f"{cost_overrun:.1f}% above sanctioned amount"
            )

        elif cost_overrun >= 30:
            reasons.append(
                f"Material cost overrun of "
                f"{cost_overrun:.1f}% above sanctioned amount"
            )

        else:
            reasons.append(
                f"Cost overrun of "
                f"{cost_overrun:.1f}% above sanctioned amount"
            )

    # --------------------------------------------------------
    # Delay
    # --------------------------------------------------------

    delay_score = safe_float(
        row.get("delay_score"),
        0.0,
    )

    delay_pct = safe_float(
        row.get("delay_pct"),
        0.0,
    )

    if delay_score > 0:

        if delay_pct >= 60:
            reasons.append(
                f"Significant execution delay of "
                f"{delay_pct:.1f}% beyond planned duration"
            )

        elif delay_pct >= 30:
            reasons.append(
                f"Material execution delay of "
                f"{delay_pct:.1f}% beyond planned duration"
            )

        else:
            reasons.append(
                f"Execution delay of "
                f"{delay_pct:.1f}% beyond planned duration"
            )

    # --------------------------------------------------------
    # Duplicate / similarity
    # --------------------------------------------------------

    duplicate_score = safe_float(
        row.get("duplicate_score"),
        0.0,
    )

    similarity = safe_float(
        row.get("max_similarity_pct"),
        0.0,
    )

    if duplicate_score > 0:

        if similarity >= 95:
            reasons.append(
                f"Very high work-description similarity detected "
                f"({similarity:.1f}%)"
            )

        elif similarity >= 90:
            reasons.append(
                f"High work-description similarity detected "
                f"({similarity:.1f}%)"
            )

        else:
            reasons.append(
                f"Similar work description detected "
                f"({similarity:.1f}% similarity)"
            )

    # --------------------------------------------------------
    # Spending pattern
    # --------------------------------------------------------

    spending_score = safe_float(
        row.get("spending_score"),
        0.0,
    )

    zscore = safe_float(
        row.get("spending_zscore"),
        0.0,
    )

    category = str(
        row.get(
            "category",
            "project",
        )
    )

    if spending_score > 0:

        if zscore >= 3:
            reasons.append(
                f"Expenditure is strongly above the "
                f"{category} category pattern "
                f"(z-score: {zscore:.2f})"
            )

        elif zscore >= 2:
            reasons.append(
                f"Expenditure is notably above the "
                f"{category} category pattern "
                f"(z-score: {zscore:.2f})"
            )

        else:
            reasons.append(
                f"Expenditure is above the "
                f"{category} category baseline "
                f"(z-score: {zscore:.2f})"
            )

    # --------------------------------------------------------
    # No significant signal
    # --------------------------------------------------------

    if not reasons:
        reasons.append(
            "No major anomaly signals detected"
        )

    return " | ".join(reasons)


# ============================================================
# ISOLATION FOREST
# ============================================================

def calculate_isolation_forest_scores(projects):
    """
    Run Isolation Forest on numerical project features.

    The model identifies projects that are unusual compared
    with the rest of the dataset.

    Important:
        - This is an unsupervised anomaly detector.
        - It does NOT determine fraud.
        - It does NOT replace the existing explainable score.
    """

    feature_candidates = [
        "estimated_cost_lakh",
        "sanctioned_amount_lakh",
        "expenditure_lakh",
        "planned_duration_days",
        "elapsed_days",
        "sanction_overrun_pct",
        "delay_pct",
        "max_similarity_pct",
        "spending_zscore",
    ]

    # --------------------------------------------------------
    # Select only features available in the dataset
    # --------------------------------------------------------

    features = [
        column
        for column in feature_candidates
        if column in projects.columns
    ]

    if len(features) < 2:
        raise ValueError(
            "Isolation Forest requires at least "
            "two usable numerical features."
        )

    print("\nIsolation Forest Features")
    print("=" * 80)

    for feature in features:
        print(f"- {feature}")

    # --------------------------------------------------------
    # Convert to numeric
    # --------------------------------------------------------

    X = projects[features].copy()

    for column in features:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Replace infinite values
    # --------------------------------------------------------

    X = X.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    )

    # --------------------------------------------------------
    # Impute missing values using median
    # --------------------------------------------------------

    imputer = SimpleImputer(
        strategy="median"
    )

    X_imputed = imputer.fit_transform(
        X
    )

    # --------------------------------------------------------
    # Build model
    # --------------------------------------------------------

    model = IsolationForest(
        n_estimators=200,
        contamination=ISOLATION_CONTAMINATION,
        random_state=ISOLATION_RANDOM_STATE,
        n_jobs=-1,
    )

    # --------------------------------------------------------
    # Train and predict
    # --------------------------------------------------------

    predictions = model.fit_predict(
        X_imputed
    )

    decision_scores = model.decision_function(
        X_imputed
    )

    # --------------------------------------------------------
    # Convert Isolation Forest output
    #
    # sklearn:
    #   +1 = normal
    #   -1 = anomaly
    #
    # More negative decision scores indicate stronger
    # anomaly behavior.
    # --------------------------------------------------------

    anomaly_strength = -decision_scores

    min_score = anomaly_strength.min()
    max_score = anomaly_strength.max()

    if max_score != min_score:

        anomaly_score_100 = (
            (
                anomaly_strength
                - min_score
            )
            / (
                max_score
                - min_score
            )
        ) * 100

    else:

        anomaly_score_100 = pd.Series(
            0,
            index=projects.index,
            dtype=float,
        )

    # --------------------------------------------------------
    # Add ML outputs
    # --------------------------------------------------------

    projects["isolation_prediction"] = (
        predictions
    )

    projects["isolation_flag"] = (
        predictions == -1
    )

    projects["isolation_anomaly_score"] = (
        pd.Series(
            anomaly_score_100,
            index=projects.index,
        )
        .clip(
            lower=0,
            upper=100,
        )
        .round(2)
    )

    return projects


# ============================================================
# BUILD RISK ENGINE
# ============================================================

def build_risk_engine():
    """
    Build the complete project-level PRISM AI
    risk dataset.
    """

    (
        projects,
        duplicate_signals,
        spending_results,
    ) = load_data()

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
            "Main dataset is missing columns: "
            f"{missing_columns}"
        )

    # ========================================================
    # ENSURE NUMERICAL COLUMNS ARE NUMERIC
    # ========================================================

    numerical_columns = [
        "estimated_cost_lakh",
        "sanctioned_amount_lakh",
        "expenditure_lakh",
        "planned_duration_days",
        "elapsed_days",
    ]

    for column in numerical_columns:
        projects[column] = pd.to_numeric(
            projects[column],
            errors="coerce",
        )

    # ========================================================
    # COST SIGNAL
    # ========================================================

    sanctioned = projects[
        "sanctioned_amount_lakh"
    ].replace(
        0,
        pd.NA,
    )

    projects["sanction_overrun_pct"] = (
        (
            projects["expenditure_lakh"]
            - projects["sanctioned_amount_lakh"]
        )
        / sanctioned
    ) * 100

    projects["sanction_overrun_pct"] = (
        projects["sanction_overrun_pct"]
        .replace(
            [float("inf"), float("-inf")],
            pd.NA,
        )
        .fillna(0)
    )

    # ========================================================
    # DELAY SIGNAL
    # ========================================================

    projects["delay_days"] = (
        projects["elapsed_days"]
        - projects["planned_duration_days"]
    )

    planned_duration = (
        projects[
            "planned_duration_days"
        ]
        .replace(
            0,
            pd.NA,
        )
    )

    projects["delay_pct"] = (
        projects["delay_days"]
        / planned_duration
    ) * 100

    projects["delay_pct"] = (
        projects["delay_pct"]
        .replace(
            [float("inf"), float("-inf")],
            pd.NA,
        )
        .fillna(0)
    )

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
        how="left",
    )

    projects["max_similarity_pct"] = (
        pd.to_numeric(
            projects["max_similarity_pct"],
            errors="coerce",
        )
        .fillna(0)
    )

    projects["similar_project_count"] = (
        pd.to_numeric(
            projects["similar_project_count"],
            errors="coerce",
        )
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
        how="left",
    )

    projects["spending_zscore"] = (
        pd.to_numeric(
            projects["spending_zscore"],
            errors="coerce",
        )
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
        axis=1,
    )

    projects["delay_score"] = projects.apply(
        calculate_delay_score,
        axis=1,
    )

    projects["duplicate_score"] = projects.apply(
        calculate_duplicate_score,
        axis=1,
    )

    projects["spending_score"] = projects.apply(
        calculate_spending_score,
        axis=1,
    )

    # ========================================================
    # EXPLAINABLE RISK SCORE
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
        .clip(
            lower=0,
            upper=100,
        )
    )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    projects["risk_level"] = projects[
        "risk_score"
    ].apply(
        get_risk_level
    )

    # ========================================================
    # EXPLANATIONS
    # ========================================================

    projects["risk_reasons"] = projects.apply(
        build_risk_reasons,
        axis=1,
    )

    # ========================================================
    # ISOLATION FOREST
    # ========================================================

    projects = calculate_isolation_forest_scores(
        projects
    )

    return projects


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 80)
    print(
        "              PRISM AI — RISK INTELLIGENCE ENGINE"
    )
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

        print(
            "\nERROR while building the Risk Engine."
        )

        print(error)
        return

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    output_folder = Path(
        "backend/data"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        f"\nProjects analyzed: {len(results)}"
    )

    # --------------------------------------------------------
    # Rule-based risk distribution
    # --------------------------------------------------------

    print("\nRisk Distribution")
    print("=" * 80)

    risk_distribution = (
        results["risk_level"]
        .value_counts()
        .reindex(
            [
                "High",
                "Medium",
                "Low",
            ],
            fill_value=0,
        )
    )

    print(
        risk_distribution.to_string()
    )

    # --------------------------------------------------------
    # Isolation Forest summary
    # --------------------------------------------------------

    print("\nIsolation Forest Results")
    print("=" * 80)

    isolation_count = int(
        results["isolation_flag"]
        .sum()
    )

    print(
        f"ML anomalies detected : "
        f"{isolation_count}"
    )

    print(
        f"ML anomaly percentage : "
        f"{(isolation_count / len(results) * 100):.2f}%"
    )

    # ========================================================
    # TOP PRIORITY PROJECTS
    # ========================================================

    top_projects = (
        results
        .sort_values(
            "risk_score",
            ascending=False,
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
        "isolation_anomaly_score",
        "isolation_flag",
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
    # TOP ML ANOMALIES
    # ========================================================

    top_ml_anomalies = (
        results
        .sort_values(
            "isolation_anomaly_score",
            ascending=False,
        )
        .head(10)
    )

    print("\nTop 10 ML Anomalies")
    print("=" * 80)

    ml_display_columns = [
        "project_id",
        "category",
        "risk_score",
        "risk_level",
        "isolation_anomaly_score",
        "isolation_flag",
    ]

    print(
        top_ml_anomalies[
            ml_display_columns
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
        f"Maximum Cost Score      : "
        f"{COST_WEIGHT}"
    )

    print(
        f"Maximum Delay Score     : "
        f"{DELAY_WEIGHT}"
    )

    print(
        f"Maximum Duplicate Score : "
        f"{DUPLICATE_WEIGHT}"
    )

    print(
        f"Maximum Spending Score  : "
        f"{SPENDING_WEIGHT}"
    )

    print(
        f"Maximum Total Score     : "
        f"{COST_WEIGHT + DELAY_WEIGHT + DUPLICATE_WEIGHT + SPENDING_WEIGHT}"
    )

    print(
        f"\nSpending anomaly starts at z-score : "
        f"{SPENDING_MIN_ZSCORE}"
    )

    print(
        f"Spending maximum score at z-score : "
        f"{SPENDING_FULL_SCORE_AT}"
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print("\nOutput file created:")
    print(OUTPUT_PATH)

    print(
        "\nPRISM AI risk engine completed successfully."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()