"""
PRISM AI - End-to-End Pipeline Runner

Pipeline:
    MPLADS Source
        ↓
    Data Transformation
        ↓
    PostgreSQL Sync
        ↓
    Spending Anomaly Detection
        ↓
    Duplicate Detection
        ↓
    Risk Engine

Usage:

    Dry run:
        python backend/services/prism_pipeline.py ^
            --source backend/data/mplads_demo_expanded.csv

    Write/update projects:
        python backend\services\prism_pipeline.py ^
            --source backend\data\mplads_demo_expanded.csv ^
            --sync
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SYNC_SCRIPT = (
    PROJECT_ROOT
    / "backend"
    / "ingestion"
    / "mplads_sync.py"
)

SPENDING_SCRIPT = (
    PROJECT_ROOT
    / "ml"
    / "spending_anomaly.py"
)

DUPLICATE_SCRIPT = (
    PROJECT_ROOT
    / "ml"
    / "duplicate_detection.py"
)

RISK_SCRIPT = (
    PROJECT_ROOT
    / "ml"
    / "risk_engine.py"
)


# -------------------------------------------------------------------
# Runner helper
# -------------------------------------------------------------------

def run_stage(
    title: str,
    script: Path,
    extra_args: list[str] | None = None,
) -> None:
    """Run one pipeline stage."""

    print("\n" + "=" * 60)
    print(f" PRISM AI - {title}")
    print("=" * 60)

    if not script.exists():
        raise FileNotFoundError(
            f"Pipeline script not found: {script}"
        )

    command = [
        sys.executable,
        str(script),
    ]

    if extra_args:
        command.extend(extra_args)

    print(
        "[PRISM AI] Running:",
        " ".join(command),
    )

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{title} failed with exit code "
            f"{result.returncode}"
        )

    print(
        f"[PRISM AI] {title} completed successfully."
    )


# -------------------------------------------------------------------
# Main pipeline
# -------------------------------------------------------------------

def run_pipeline(
    source: str,
    sync_database: bool = False,
) -> None:

    print("\n")
    print("=" * 60)
    print("              PRISM AI PIPELINE")
    print("=" * 60)
    print(f"Source: {source}")
    print(
        f"Database write: "
        f"{'ENABLED' if sync_database else 'DRY RUN'}"
    )

    # ---------------------------------------------------------------
    # 1. Source ingestion + transformation + DB comparison
    # ---------------------------------------------------------------

    sync_args = [
        "--source",
        source,
    ]

    if sync_database:
        sync_args.append("--write")

    run_stage(
        "SOURCE + DATABASE SYNC",
        SYNC_SCRIPT,
        sync_args,
    )

    # ---------------------------------------------------------------
    # 2. Spending anomaly detection
    # ---------------------------------------------------------------

    run_stage(
        "SPENDING ANOMALY DETECTION",
        SPENDING_SCRIPT,
    )

    # ---------------------------------------------------------------
    # 3. Duplicate detection
    # ---------------------------------------------------------------

    run_stage(
        "DUPLICATE DETECTION",
        DUPLICATE_SCRIPT,
    )

    # ---------------------------------------------------------------
    # 4. Risk engine
    # ---------------------------------------------------------------

    run_stage(
        "RISK ENGINE",
        RISK_SCRIPT,
    )

    # ---------------------------------------------------------------
    # 5. Complete
    # ---------------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("          PRISM AI PIPELINE COMPLETE")
    print("=" * 60)

    print("\nStages completed:")
    print("  [1] Source ingestion")
    print("  [2] Data transformation")
    print("  [3] Database synchronization")
    print("  [4] Spending anomaly detection")
    print("  [5] Duplicate detection")
    print("  [6] Risk analysis")

    print("\nPRISM AI processing completed successfully.")


# -------------------------------------------------------------------
# Command-line interface
# -------------------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser(
        description="PRISM AI end-to-end pipeline"
    )

    parser.add_argument(
        "--source",
        required=True,
        help=(
            "CSV, Excel, JSON file path, "
            "or supported HTTP/HTTPS source"
        ),
    )

    parser.add_argument(
        "--sync",
        action="store_true",
        help=(
            "Write/update project data in PostgreSQL. "
            "Without this flag, source synchronization is a dry run."
        ),
    )

    args = parser.parse_args()

    try:

        run_pipeline(
            source=args.source,
            sync_database=args.sync,
        )

    except KeyboardInterrupt:

        print(
            "\n[PRISM AI] Pipeline interrupted by user."
        )

        raise SystemExit(1)

    except Exception as exc:

        print(
            "\n[PRISM AI] PIPELINE FAILED"
        )

        print(
            f"Reason: {exc}"
        )

        raise SystemExit(1)


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    main()