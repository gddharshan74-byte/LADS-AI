"""
PRISM AI - MPLADS Data Transformer

Converts source data into the standardized project structure
used by the PostgreSQL projects table.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


# -------------------------------------------------------------------
# Final standardized project columns
# -------------------------------------------------------------------

OUTPUT_COLUMNS = [
    "project_id",
    "mp_name",
    "state",
    "district",
    "category",
    "work_description",
    "estimated_cost_lakh",
    "sanctioned_amount_lakh",
    "expenditure_lakh",
    "physical_progress_pct",
    "planned_duration_days",
    "elapsed_days",
    "start_date",
    "expected_completion_date",
    "current_status",
    "latitude",
    "longitude",
    "implementing_agency",
    "category_avg_expenditure_lakh",
    "category_std_expenditure_lakh",
]


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _safe_numeric(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Convert a column to numeric safely."""

    if column not in df.columns:
        return pd.Series(
            [None] * len(df),
            index=df.index,
            dtype="float64",
        )

    return pd.to_numeric(
        df[column],
        errors="coerce",
    )


def _safe_text(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Return a cleaned text column."""

    if column not in df.columns:
        return pd.Series(
            [None] * len(df),
            index=df.index,
            dtype="object",
        )

    return (
        df[column]
        .astype("string")
        .str.strip()
        .replace(
            {"": pd.NA}
        )
    )


# -------------------------------------------------------------------
# Main transformation
# -------------------------------------------------------------------

def transform(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Transform a source DataFrame into standardized PRISM AI
    project records.

    Parameters
    ----------
    df:
        DataFrame returned by mplads_source.load_source()

    Returns
    -------
    list[dict]
        Database-ready project records.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "transform() expects a pandas DataFrame."
        )

    if df.empty:
        return []

    data = df.copy()

    # ---------------------------------------------------------------
    # Ensure required fields exist
    # ---------------------------------------------------------------

    required = [
        "project_id",
        "state",
        "district",
        "category",
        "work_description",
    ]

    missing = [
        column
        for column in required
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            "Transformer missing required columns: "
            + ", ".join(missing)
        )

    # ---------------------------------------------------------------
    # Text normalization
    # ---------------------------------------------------------------

    text_columns = [
        "project_id",
        "mp_name",
        "state",
        "district",
        "category",
        "work_description",
        "current_status",
        "implementing_agency",
    ]

    for column in text_columns:
        if column in data.columns:
            data[column] = (
                data[column]
                .astype("string")
                .str.strip()
            )

    # ---------------------------------------------------------------
    # Numeric normalization
    # ---------------------------------------------------------------

    numeric_columns = [
        "estimated_cost_lakh",
        "sanctioned_amount_lakh",
        "expenditure_lakh",
        "physical_progress_pct",
        "planned_duration_days",
        "elapsed_days",
        "latitude",
        "longitude",
    ]

    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

    # ---------------------------------------------------------------
    # Date normalization
    # ---------------------------------------------------------------

    date_columns = [
        "start_date",
        "expected_completion_date",
    ]

    for column in date_columns:

        if column in data.columns:

            data[column] = pd.to_datetime(
                data[column],
                errors="coerce",
            )

    # ---------------------------------------------------------------
    # Calculate category spending statistics
    #
    # These are later used by the spending anomaly module.
    # ---------------------------------------------------------------

    if "expenditure_lakh" in data.columns:

        category_stats = (
            data.groupby(
                "category",
                dropna=False,
            )["expenditure_lakh"]
            .agg(
                category_avg_expenditure_lakh="mean",
                category_std_expenditure_lakh="std",
            )
            .reset_index()
        )

        data = data.merge(
            category_stats,
            on="category",
            how="left",
        )

    else:

        data[
            "category_avg_expenditure_lakh"
        ] = None

        data[
            "category_std_expenditure_lakh"
        ] = None

    # ---------------------------------------------------------------
    # Replace infinite values
    # ---------------------------------------------------------------

    data = data.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    )

    # ---------------------------------------------------------------
    # Ensure all final columns exist
    # ---------------------------------------------------------------

    for column in OUTPUT_COLUMNS:

        if column not in data.columns:

            data[column] = None

    # ---------------------------------------------------------------
    # Keep only the standardized columns
    # ---------------------------------------------------------------

    data = data[
        OUTPUT_COLUMNS
    ].copy()

    # ---------------------------------------------------------------
    # Convert dates to Python date objects
    # for PostgreSQL / SQLAlchemy compatibility.
    # ---------------------------------------------------------------

    for column in date_columns:

        data[column] = data[column].apply(
            lambda value:
                value.date()
                if pd.notna(value)
                else None
        )

    # ---------------------------------------------------------------
    # Convert NaN / pd.NA to None
    # ---------------------------------------------------------------

    data = data.astype(object)

    data = data.where(
        pd.notna(data),
        None,
    )

    # ---------------------------------------------------------------
    # Remove completely invalid project IDs
    # ---------------------------------------------------------------

    data = data[
        data["project_id"].notna()
    ].copy()

    # ---------------------------------------------------------------
    # Remove duplicate project IDs
    #
    # Keep the last source record for the same project ID.
    # ---------------------------------------------------------------

    data = data.drop_duplicates(
        subset=["project_id"],
        keep="last",
    )

    # ---------------------------------------------------------------
    # Return database-ready records
    # ---------------------------------------------------------------

    records = data.to_dict(
        orient="records"
    )

    return records


# -------------------------------------------------------------------
# Simple standalone test
# -------------------------------------------------------------------

def main():
    """
    Basic transformer self-test.
    """

    sample = pd.DataFrame(
        [
            {
                "project_id": "TEST001",
                "mp_name": "Test MP",
                "state": "Karnataka",
                "district": "Bengaluru",
                "category": "Community Works",
                "work_description": "Construction of community hall",
                "estimated_cost_lakh": 100,
                "sanctioned_amount_lakh": 95,
                "expenditure_lakh": 90,
                "physical_progress_pct": 80,
                "planned_duration_days": 180,
                "elapsed_days": 150,
                "start_date": "2026-01-01",
                "expected_completion_date": "2026-06-30",
                "current_status": "Ongoing",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "implementing_agency": "Local Authority",
            }
        ]
    )

    result = transform(sample)

    print(
        "[PRISM AI] Transformer test passed."
    )

    print(
        f"Records produced: {len(result)}"
    )

    if result:
        print(
            "Columns produced:",
            len(result[0])
        )


if __name__ == "__main__":
    main()