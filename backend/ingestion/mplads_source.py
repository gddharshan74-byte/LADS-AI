"""
PRISM AI - MPLADS Source Ingestion

Purpose:
    Load MPLADS-like source data from:
      - CSV
      - Excel (.xlsx / .xls)
      - JSON
      - HTTP/HTTPS URL

Flow:
    Source -> Load -> Normalize -> Validate -> DataFrame

This module does NOT write directly to PostgreSQL.
Database synchronization is handled by mplads_sync.py.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd


# -------------------------------------------------------------------
# Standard PRISM AI column names
# -------------------------------------------------------------------

STANDARD_COLUMNS = [
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
]


# -------------------------------------------------------------------
# Required columns for project-level ingestion
# -------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "project_id",
    "state",
    "district",
    "category",
    "work_description",
]


# -------------------------------------------------------------------
# Common source-column aliases
# -------------------------------------------------------------------
# Different official/exported datasets may use slightly different
# names. These aliases help PRISM AI map them into one schema.

COLUMN_ALIASES = {
    "project id": "project_id",
    "projectid": "project_id",
    "project_code": "project_id",
    "project code": "project_id",
    "work id": "project_id",
    "work_id": "project_id",

    "mp": "mp_name",
    "mp name": "mp_name",
    "member name": "mp_name",
    "member of parliament": "mp_name",

    "state name": "state",
    "state_name": "state",

    "district name": "district",
    "district_name": "district",

    "work category": "category",
    "project category": "category",
    "category name": "category",

    "description": "work_description",
    "work description": "work_description",
    "work_description": "work_description",
    "project description": "work_description",

    "estimated cost": "estimated_cost_lakh",
    "estimated cost lakh": "estimated_cost_lakh",
    "estimated_cost": "estimated_cost_lakh",
    "estimated_cost_lakh": "estimated_cost_lakh",

    "sanctioned amount": "sanctioned_amount_lakh",
    "sanctioned amount lakh": "sanctioned_amount_lakh",
    "sanctioned_amount": "sanctioned_amount_lakh",
    "sanctioned_amount_lakh": "sanctioned_amount_lakh",

    "expenditure": "expenditure_lakh",
    "expenditure amount": "expenditure_lakh",
    "expenditure lakh": "expenditure_lakh",
    "expenditure_lakh": "expenditure_lakh",

    "physical progress": "physical_progress_pct",
    "physical progress %": "physical_progress_pct",
    "physical_progress": "physical_progress_pct",
    "physical_progress_pct": "physical_progress_pct",

    "planned duration": "planned_duration_days",
    "planned duration days": "planned_duration_days",
    "planned_duration": "planned_duration_days",
    "planned_duration_days": "planned_duration_days",

    "elapsed days": "elapsed_days",
    "elapsed_days": "elapsed_days",

    "start date": "start_date",
    "start_date": "start_date",

    "expected completion": "expected_completion_date",
    "expected completion date": "expected_completion_date",
    "expected_completion_date": "expected_completion_date",

    "status": "current_status",
    "current status": "current_status",
    "current_status": "current_status",

    "lat": "latitude",
    "latitude": "latitude",

    "long": "longitude",
    "lon": "longitude",
    "longitude": "longitude",

    "implementing agency": "implementing_agency",
    "implementing_agency": "implementing_agency",
    "agency": "implementing_agency",
}


# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------

def _clean_column_name(name: Any) -> str:
    """Convert a source column name into a normalized form."""

    text = str(name).strip().lower()

    replacements = {
        "-": "_",
        "/": "_",
        "\\": "_",
        ".": "_",
        "(": "",
        ")": "",
        "%": "pct",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = " ".join(text.split())

    return text.strip()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize source column names and map known aliases
    to PRISM AI standard names.
    """

    rename_map = {}

    for column in df.columns:
        cleaned = _clean_column_name(column)

        # Try direct match first
        if cleaned in COLUMN_ALIASES:
            rename_map[column] = COLUMN_ALIASES[cleaned]
            continue

        # Try underscore -> space
        alternate = cleaned.replace("_", " ")

        if alternate in COLUMN_ALIASES:
            rename_map[column] = COLUMN_ALIASES[alternate]
            continue

        # Otherwise preserve the cleaned name
        rename_map[column] = cleaned.replace(" ", "_")

    df = df.rename(columns=rename_map)

    # Remove duplicate columns produced by alias mapping
    df = df.loc[:, ~df.columns.duplicated()]

    return df


def _read_local_file(source: str | Path) -> pd.DataFrame:
    """Read CSV, Excel, or JSON from a local path."""

    path = Path(source)

    if not path.exists():
        raise FileNotFoundError(
            f"Source file not found: {path}"
        )

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)

    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        return _json_to_dataframe(payload)

    raise ValueError(
        f"Unsupported file type '{suffix}'. "
        f"Supported types: CSV, XLSX, XLS, JSON."
    )


def _read_remote_file(url: str) -> pd.DataFrame:
    """Download and read CSV, Excel, or JSON from an HTTP/HTTPS URL."""

    request = Request(
        url,
        headers={
            "User-Agent": (
                "PRISM-AI-MPLADS-Data-Ingestion/1.0"
            )
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            content = response.read()

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

    except Exception as exc:
        raise RuntimeError(
            f"Unable to download source URL: {url}\n"
            f"Reason: {exc}"
        ) from exc

    url_lower = url.lower()

    # Detect source type using URL/content type
    if (
        ".csv" in url_lower
        or "text/csv" in content_type
        or "csv" in content_type
    ):
        return pd.read_csv(io.BytesIO(content))

    if (
        ".xlsx" in url_lower
        or "spreadsheet" in content_type
        or "excel" in content_type
    ):
        return pd.read_excel(io.BytesIO(content))

    if ".xls" in url_lower:
        return pd.read_excel(io.BytesIO(content))

    if ".json" in url_lower or "application/json" in content_type:
        try:
            payload = json.loads(
                content.decode("utf-8")
            )
        except UnicodeDecodeError as exc:
            raise ValueError(
                "The remote JSON response could not be decoded as UTF-8."
            ) from exc

        return _json_to_dataframe(payload)

    # Last attempt:
    # try JSON, then CSV.
    try:
        payload = json.loads(
            content.decode("utf-8")
        )
        return _json_to_dataframe(payload)

    except Exception:
        try:
            return pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            raise ValueError(
                "Could not determine the remote data format. "
                "Please provide a CSV, Excel, or JSON source."
            ) from exc


def _json_to_dataframe(payload: Any) -> pd.DataFrame:
    """
    Convert common JSON structures into a DataFrame.

    Supported examples:

        [
            {"project_id": "P1001", ...},
            {"project_id": "P1002", ...}
        ]

    or:

        {
            "data": [
                {...},
                {...}
            ]
        }

    or:

        {
            "results": [
                {...},
                {...}
            ]
        }
    """

    if isinstance(payload, list):
        return pd.DataFrame(payload)

    if isinstance(payload, dict):

        for key in [
            "data",
            "results",
            "records",
            "projects",
            "items",
        ]:
            value = payload.get(key)

            if isinstance(value, list):
                return pd.DataFrame(value)

        # Single object
        return pd.DataFrame([payload])

    raise ValueError(
        "Unsupported JSON structure. "
        "Expected a list of records or an object containing "
        "'data', 'results', 'records', 'projects', or 'items'."
    )


# -------------------------------------------------------------------
# Cleaning
# -------------------------------------------------------------------

def _clean_values(df: pd.DataFrame) -> pd.DataFrame:
    """Clean whitespace, empty values, numeric fields and dates."""

    df = df.copy()

    # Convert empty strings to NaN
    df = df.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    # Strip whitespace from text columns
    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # Numeric fields
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

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Date fields
    date_columns = [
        "start_date",
        "expected_completion_date",
    ]

    for column in date_columns:

        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    return df


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

def validate_source_data(
    df: pd.DataFrame,
    source_name: str = "source",
) -> dict[str, Any]:
    """
    Validate the incoming dataset.

    Returns a validation report rather than immediately
    failing for every non-critical issue.
    """

    if df.empty:
        raise ValueError(
            f"{source_name} contains no records."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    report = {
        "source": source_name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_required_columns": missing_columns,
        "duplicate_project_ids": 0,
        "missing_project_ids": 0,
        "missing_work_descriptions": 0,
        "missing_categories": 0,
        "status": "valid",
    }

    if "project_id" in df.columns:

        missing_project_ids = int(
            df["project_id"].isna().sum()
        )

        duplicate_project_ids = int(
            df["project_id"]
            .dropna()
            .duplicated()
            .sum()
        )

        report["missing_project_ids"] = (
            missing_project_ids
        )

        report["duplicate_project_ids"] = (
            duplicate_project_ids
        )

    if "work_description" in df.columns:
        report["missing_work_descriptions"] = int(
            df["work_description"].isna().sum()
        )

    if "category" in df.columns:
        report["missing_categories"] = int(
            df["category"].isna().sum()
        )

    # Critical problems
    if report["missing_project_ids"] > 0:
        report["status"] = "warning"

    if report["duplicate_project_ids"] > 0:
        report["status"] = "warning"

    return report


# -------------------------------------------------------------------
# Main ingestion function
# -------------------------------------------------------------------

def load_source(
    source: str | Path,
    validate: bool = True,
) -> pd.DataFrame:
    """
    Load, normalize, clean and validate a source.

    Parameters
    ----------
    source:
        Local file path or HTTP/HTTPS URL.

    validate:
        Whether to run source validation.

    Returns
    -------
    pandas.DataFrame
        Normalized PRISM AI project dataset.
    """

    source_text = str(source).strip()

    if not source_text:
        raise ValueError(
            "A source path or URL is required."
        )

    # Determine local vs remote
    if source_text.startswith(
        ("http://", "https://")
    ):
        print(
            f"[PRISM AI] Loading remote source: {source_text}"
        )

        df = _read_remote_file(source_text)

    else:
        print(
            f"[PRISM AI] Loading local source: {source_text}"
        )

        df = _read_local_file(source_text)

    # Normalize columns
    df = _normalize_columns(df)

    # Clean values
    df = _clean_values(df)

    # Validate
    if validate:

        report = validate_source_data(
            df,
            source_name=source_text,
        )

        print(
            "[PRISM AI] Validation:",
            report["status"]
        )

        print(
            "[PRISM AI] Rows:",
            report["rows"]
        )

        print(
            "[PRISM AI] Columns:",
            report["columns"]
        )

        if report["missing_required_columns"]:
            print(
                "[PRISM AI] Missing:",
                report["missing_required_columns"]
            )

        if report["duplicate_project_ids"]:
            print(
                "[PRISM AI] Duplicate project IDs:",
                report["duplicate_project_ids"]
            )

    return df


# -------------------------------------------------------------------
# Convenience helpers
# -------------------------------------------------------------------

def get_source_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Return a compact summary useful for the ingestion pipeline."""

    summary = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "project_count": (
            int(df["project_id"].nunique())
            if "project_id" in df.columns
            else 0
        ),
        "states": (
            int(df["state"].nunique())
            if "state" in df.columns
            else 0
        ),
        "districts": (
            int(df["district"].nunique())
            if "district" in df.columns
            else 0
        ),
        "categories": (
            int(df["category"].nunique())
            if "category" in df.columns
            else 0
        ),
    }

    return summary


# -------------------------------------------------------------------
# Command-line test
# -------------------------------------------------------------------

def main() -> None:
    """
    Example:

        python backend\\ingestion\\mplads_source.py ^
            --source backend\\data\\mplads_demo_expanded.csv
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="PRISM AI MPLADS source ingestion"
    )

    parser.add_argument(
        "--source",
        required=True,
        help=(
            "Path or URL to CSV, Excel, or JSON source"
        ),
    )

    args = parser.parse_args()

    try:

        df = load_source(args.source)

        summary = get_source_summary(df)

        print("\n[PRISM AI] Source Summary")
        print("-------------------------")

        for key, value in summary.items():
            print(f"{key}: {value}")

        print("\n[PRISM AI] Standardized Columns")
        print("-------------------------------")

        for column in df.columns:
            print(f"- {column}")

        print(
            "\n[PRISM AI] Source ingestion completed successfully."
        )

    except Exception as exc:

        print(
            "\n[PRISM AI] Source ingestion failed:"
        )

        print(exc)

        raise SystemExit(1)


if __name__ == "__main__":
    main()