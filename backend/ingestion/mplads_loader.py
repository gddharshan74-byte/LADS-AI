"""
PRISM AI - MPLADS Data Loader

Purpose:
    Load MPLADS source data from CSV or Excel files.

This module is intentionally separated from:
    - data transformation
    - database insertion
    - AI/risk analysis

That separation allows PRISM AI to later accept:
    - official CSV files
    - official Excel files
    - downloaded datasets
    - future authorized API responses

without changing the downstream analytics pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd


SourceType = Union[str, Path]


class MPLADSDataLoader:
    """Loads MPLADS source data into a pandas DataFrame."""

    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}

    def load(self, source: SourceType, sheet_name: Union[int, str] = 0) -> pd.DataFrame:
        """
        Load data from a local file or a URL.

        Parameters
        ----------
        source:
            Local file path or HTTP/HTTPS URL.

        sheet_name:
            Excel sheet index or sheet name.
            Ignored for CSV/JSON sources.

        Returns
        -------
        pandas.DataFrame
            Loaded source data.

        Raises
        ------
        FileNotFoundError
            If a local source does not exist.

        ValueError
            If the source type is unsupported or no records are found.

        RuntimeError
            If pandas fails to read the source.
        """

        source_str = str(source).strip()

        if not source_str:
            raise ValueError("MPLADS data source cannot be empty.")

        # ---------------------------------------------------------
        # URL SOURCE
        # ---------------------------------------------------------
        if source_str.startswith(("http://", "https://")):
            return self._load_from_url(source_str, sheet_name)

        # ---------------------------------------------------------
        # LOCAL FILE SOURCE
        # ---------------------------------------------------------
        path = Path(source_str)

        if not path.exists():
            raise FileNotFoundError(
                f"MPLADS source file was not found: {path.resolve()}"
            )

        if not path.is_file():
            raise ValueError(
                f"MPLADS source path is not a file: {path.resolve()}"
            )

        return self._load_file(path, sheet_name)

    # =============================================================
    # LOCAL FILE LOADING
    # =============================================================

    def _load_file(
        self,
        path: Path,
        sheet_name: Union[int, str] = 0,
    ) -> pd.DataFrame:
        """Load a supported local file."""

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported MPLADS file type: '{extension}'. "
                f"Supported types: {sorted(self.SUPPORTED_EXTENSIONS)}"
            )

        try:
            if extension == ".csv":
                df = pd.read_csv(path)

            elif extension in {".xlsx", ".xls"}:
                df = pd.read_excel(path, sheet_name=sheet_name)

            elif extension == ".json":
                df = pd.read_json(path)

            else:
                raise ValueError(
                    f"Unsupported MPLADS source extension: {extension}"
                )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load MPLADS source file '{path}': {exc}"
            ) from exc

        return self._prepare_dataframe(df)

    # =============================================================
    # URL LOADING
    # =============================================================

    def _load_from_url(
        self,
        url: str,
        sheet_name: Union[int, str] = 0,
    ) -> pd.DataFrame:
        """
        Load data from an HTTP/HTTPS source.

        The actual official source URL will be configured later once
        the authorized MPLADS data access mechanism is established.
        """

        try:
            lower_url = url.lower().split("?", maxsplit=1)[0]

            if lower_url.endswith(".csv"):
                df = pd.read_csv(url)

            elif lower_url.endswith((".xlsx", ".xls")):
                df = pd.read_excel(url, sheet_name=sheet_name)

            elif lower_url.endswith(".json"):
                df = pd.read_json(url)

            else:
                raise ValueError(
                    "Unable to determine the data format from the URL. "
                    "Provide a CSV, XLSX, XLS, or JSON source."
                )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load MPLADS data from URL '{url}': {exc}"
            ) from exc

        return self._prepare_dataframe(df)

    # =============================================================
    # BASIC DATA PREPARATION
    # =============================================================

    @staticmethod
    def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform safe loader-level preparation.

        This does NOT perform MPLADS-specific field mapping.
        That responsibility belongs to mplads_transformer.py.
        """

        if df is None:
            raise ValueError("The MPLADS loader received no DataFrame.")

        if df.empty:
            raise ValueError("The MPLADS source contains no records.")

        # Work on a copy so the caller's DataFrame is never modified.
        df = df.copy()

        # Remove accidental whitespace around column names.
        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        # Remove completely empty rows.
        df = df.dropna(how="all").reset_index(drop=True)

        if df.empty:
            raise ValueError(
                "The MPLADS source contains no usable records "
                "after removing empty rows."
            )

        return df

    # =============================================================
    # INFORMATION / PREVIEW
    # =============================================================

    @staticmethod
    def describe(df: pd.DataFrame) -> dict:
        """
        Return a compact description of loaded source data.
        """

        return {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": [str(column) for column in df.columns],
        }


# ================================================================
# SIMPLE MANUAL TEST
# ================================================================

if __name__ == "__main__":
    """
    Development test using the current synthetic MPLADS-like dataset.

    This test only READS the CSV.
    It does not modify PostgreSQL or any existing project data.
    """

    project_root = Path(__file__).resolve().parents[2]

    sample_source = (
        project_root
        / "backend"
        / "data"
        / "mplads_demo_expanded.csv"
    )

    loader = MPLADSDataLoader()

    try:
        dataframe = loader.load(sample_source)

        info = loader.describe(dataframe)

        print("=" * 60)
        print("PRISM AI MPLADS DATA LOADER TEST")
        print("=" * 60)

        print(f"Source: {sample_source}")
        print(f"Rows loaded: {info['rows']}")
        print(f"Columns loaded: {info['columns']}")

        print("\nColumns:")
        for column in info["column_names"]:
            print(f"  - {column}")

        print("\nFirst 5 records:")
        print(dataframe.head().to_string(index=False))

        print("\nMPLADS loader test completed successfully.")

    except Exception as exc:
        print("\nMPLADS loader test failed.")
        print(f"Error: {exc}")
        raise