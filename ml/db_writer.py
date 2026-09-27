import sys
from pathlib import Path

import pandas as pd


# Make the backend folder importable when this file
# is executed through the ML module.
PROJECT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from database import SessionLocal
from models.database_models import (
    RiskResult,
    SpendingAnalysis,
    DuplicateSignal,
)


def _to_float(value):
    """Convert a value safely to float."""
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    """Convert a value safely to integer."""
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value):
    """Convert CSV/Pandas boolean-like values safely."""
    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    value = str(value).strip().lower()

    if value in {"true", "1", "yes", "y"}:
        return True

    if value in {"false", "0", "no", "n"}:
        return False

    return None


def _to_text(value):
    """Convert a value safely to text."""
    if pd.isna(value):
        return None

    return str(value)


def save_risk_results(df: pd.DataFrame):
    """
    Replace the PostgreSQL risk_results table
    with the latest PRISM AI risk-engine results.
    """

    db = SessionLocal()

    try:
        db.query(RiskResult).delete()

        records = []

        for _, row in df.iterrows():
            record = RiskResult(
                project_id=_to_text(row.get("project_id")),

                sanction_overrun_pct=_to_float(
                    row.get("sanction_overrun_pct")
                ),

                delay_pct=_to_float(
                    row.get("delay_pct")
                ),

                max_similarity_pct=_to_float(
                    row.get("max_similarity_pct")
                ),

                similar_project_count=_to_int(
                    row.get("similar_project_count")
                ),

                duplicate_signal=_to_bool(
                    row.get("duplicate_signal")
                ),

                spending_zscore=_to_float(
                    row.get("spending_zscore")
                ),

                spending_anomaly=_to_bool(
                    row.get("spending_anomaly")
                ),

                cost_score=_to_float(
                    row.get("cost_score")
                ),

                delay_score=_to_float(
                    row.get("delay_score")
                ),

                duplicate_score=_to_float(
                    row.get("duplicate_score")
                ),

                spending_score=_to_float(
                    row.get("spending_score")
                ),

                risk_score=_to_float(
                    row.get("risk_score")
                ),

                risk_level=_to_text(
                    row.get("risk_level")
                ),

                risk_reasons=_to_text(
                    row.get("risk_reasons")
                ),

                isolation_prediction=_to_int(
                    row.get("isolation_prediction")
                ),

                isolation_flag=_to_bool(
                    row.get("isolation_flag")
                ),

                isolation_anomaly_score=_to_float(
                    row.get("isolation_anomaly_score")
                ),
            )

            records.append(record)

        db.add_all(records)
        db.commit()

        return len(records)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def save_spending_results(df: pd.DataFrame):
    """
    Replace PostgreSQL spending-analysis results
    with the latest spending detector output.
    """

    db = SessionLocal()

    try:
        db.query(SpendingAnalysis).delete()

        records = []

        for _, row in df.iterrows():
            records.append(
                SpendingAnalysis(
                    project_id=_to_text(row.get("project_id")),
                    spending_zscore=_to_float(
                        row.get("spending_zscore")
                    ),
                    spending_anomaly=_to_bool(
                        row.get("spending_anomaly")
                    ),
                )
            )

        db.add_all(records)
        db.commit()

        return len(records)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def save_duplicate_results(df: pd.DataFrame):
    """
    Replace PostgreSQL duplicate-signal results
    with the latest duplicate detector output.
    """

    db = SessionLocal()

    try:
        db.query(DuplicateSignal).delete()

        records = []

        for _, row in df.iterrows():
            records.append(
                DuplicateSignal(
                    project_id=_to_text(row.get("project_id")),
                    max_similarity_pct=_to_float(
                        row.get("max_similarity_pct")
                    ),
                    similar_project_count=_to_int(
                        row.get("similar_project_count")
                    ),
                    duplicate_signal=_to_bool(
                        row.get("duplicate_signal")
                    ),
                )
            )

        db.add_all(records)
        db.commit()

        return len(records)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()