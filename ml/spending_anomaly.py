"""
PRISM AI - Spending Anomaly Detection

Purpose:
    Detect unusually high expenditure compared with projects
    in the same category.

Primary data source:
    PostgreSQL

Prototype threshold:
    Z-score >= 2.0

Important:
    This is an analytical prototype threshold and is NOT
    an official MPLADS threshold.

Pipeline:

    PostgreSQL
        ↓
    Spending Analysis
        ↓
    Z-score calculation
        ↓
    Anomaly detection
        ↓
    PostgreSQL
        ↓
    CSV backup
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


# ================================================================
# PROJECT PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"

# Add project root first.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add backend so database/model imports use one consistent module path.
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# ================================================================
# PRISM AI IMPORTS
# ================================================================

# IMPORTANT:
# Use the same module paths as ml/db_writer.py to avoid loading
# database_models.py twice under different module names.
from database import SessionLocal
from models.database_models import Project
from ml.db_writer import save_spending_results


# ================================================================
# CONFIGURATION
# ================================================================

# Prototype threshold.
# This is NOT an official MPLADS threshold.
ZSCORE_THRESHOLD = 2.0

# CSV backup/export only.
# PostgreSQL remains the primary data store.
OUTPUT_PATH = (
    BACKEND_ROOT
    / "data"
    / "spending_results.csv"
)


# ================================================================
# LOAD PROJECT DATA FROM POSTGRESQL
# ================================================================

def load_projects_from_database() -> pd.DataFrame:
    """
    Load project data required for spending analysis
    directly from PostgreSQL.
    """

    db = SessionLocal()

    try:
        projects = (
            db.query(
                Project.project_id,
                Project.category,
                Project.expenditure_lakh,
            )
            .all()
        )

        records = [
            {
                "project_id": project.project_id,
                "category": project.category,
                "expenditure_lakh": project.expenditure_lakh,
            }
            for project in projects
        ]

        df = pd.DataFrame(records)

        if df.empty:
            raise ValueError(
                "No project records were found in PostgreSQL."
            )

        # Make sure expenditure is numeric.
        df["expenditure_lakh"] = pd.to_numeric(
            df["expenditure_lakh"],
            errors="coerce",
        )

        return df

    finally:
        db.close()


# ================================================================
# SPENDING ANOMALY DETECTION
# ================================================================

def detect_spending_anomalies(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect unusually high expenditure compared with projects
    in the same category.

    A project is flagged when its expenditure is at least
    2 standard deviations above the category mean.
    """

    if df is None or df.empty:
        raise ValueError(
            "Cannot perform spending analysis on empty data."
        )

    result = df.copy()

    # ------------------------------------------------------------
    # Category mean
    # ------------------------------------------------------------

    result["category_avg_expenditure_lakh"] = (
        result.groupby("category")[
            "expenditure_lakh"
        ].transform("mean")
    )

    # ------------------------------------------------------------
    # Category standard deviation
    # ------------------------------------------------------------

    result["category_std_expenditure_lakh"] = (
        result.groupby("category")[
            "expenditure_lakh"
        ].transform("std")
    )

    # ------------------------------------------------------------
    # Spending Z-score
    # ------------------------------------------------------------

    safe_std = (
        result["category_std_expenditure_lakh"]
        .replace(0, pd.NA)
    )

    result["spending_zscore"] = (
        (
            result["expenditure_lakh"]
            - result["category_avg_expenditure_lakh"]
        )
        / safe_std
    )

    # ------------------------------------------------------------
    # Spending anomaly flag
    # ------------------------------------------------------------

    result["spending_anomaly"] = (
        result["spending_zscore"]
        >= ZSCORE_THRESHOLD
    ).fillna(False)

    return result


# ================================================================
# SAVE CSV BACKUP
# ================================================================

def save_csv_backup(result: pd.DataFrame) -> None:
    """
    Save an export for backup/debugging.

    PostgreSQL remains the primary analytical data store.
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )


# ================================================================
# MAIN
# ================================================================

def main():

    print()
    print("=" * 80)
    print("PRISM AI - SPENDING PATTERN ANALYSIS")
    print("=" * 80)

    # ------------------------------------------------------------
    # STEP 1: Load from PostgreSQL
    # ------------------------------------------------------------

    print()
    print("Loading project data from PostgreSQL...")

    df = load_projects_from_database()

    print(
        f"Projects loaded from PostgreSQL: {len(df)}"
    )

    # ------------------------------------------------------------
    # STEP 2: Run spending analysis
    # ------------------------------------------------------------

    print()
    print("Running category-based spending analysis...")

    result = detect_spending_anomalies(df)

    print(
        f"Z-score threshold: {ZSCORE_THRESHOLD}"
    )

    # ------------------------------------------------------------
    # STEP 3: Display top results
    # ------------------------------------------------------------

    columns = [
        "project_id",
        "category",
        "expenditure_lakh",
        "category_avg_expenditure_lakh",
        "category_std_expenditure_lakh",
        "spending_zscore",
        "spending_anomaly",
    ]

    print()
    print("Top Spending Patterns")
    print("=" * 80)

    top_results = (
        result[columns]
        .sort_values(
            "spending_zscore",
            ascending=False,
            na_position="last",
        )
        .head(20)
        .copy()
    )

    print(
        top_results
        .round(2)
        .to_string(index=False)
    )

    # ------------------------------------------------------------
    # STEP 4: Display anomalies
    # ------------------------------------------------------------

    anomalies = result[
        result["spending_anomaly"]
    ].copy()

    print()
    print("Potential Spending Pattern Anomalies")
    print("=" * 80)

    if anomalies.empty:

        print(
            "No unusual spending patterns detected."
        )

    else:

        for _, row in anomalies.iterrows():

            z_score = row["spending_zscore"]

            if pd.isna(z_score):
                continue

            print(
                f"{row['project_id']} | "
                f"{row['category']} | "
                f"Expenditure: "
                f"₹{row['expenditure_lakh']:.2f}L | "
                f"Category average: "
                f"₹{row['category_avg_expenditure_lakh']:.2f}L | "
                f"Z-score: {z_score:.2f}"
            )

    # ------------------------------------------------------------
    # STEP 5: Save to PostgreSQL
    # ------------------------------------------------------------

    print()
    print("Writing spending analysis to PostgreSQL...")

    save_spending_results(result)

    print(
        f"Spending analysis written to PostgreSQL: "
        f"{len(result)}"
    )

    # ------------------------------------------------------------
    # STEP 6: Save CSV backup
    # ------------------------------------------------------------

    save_csv_backup(result)

    print()
    print("CSV backup created:")
    print(OUTPUT_PATH)

    # ------------------------------------------------------------
    # COMPLETE
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("PRISM AI SPENDING ANALYSIS COMPLETED")
    print("=" * 80)


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()