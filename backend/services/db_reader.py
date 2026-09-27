"""
PRISM AI - PostgreSQL Database Reader

Purpose:
    Provide a clean database-reading layer for the FastAPI backend.

The API imports this module through:

    backend.services.db_reader

Therefore all database/model imports use the fully qualified
backend.* package path to avoid Python module duplication.
"""

from __future__ import annotations

from typing import Any

from backend.database import SessionLocal
from backend.models.database_models import (
    Project,
    RiskResult,
    SpendingAnalysis,
)


# ================================================================
# VALUE HELPERS
# ================================================================

def clean_value(value: Any) -> Any:
    """
    Convert SQLAlchemy / pandas-like values into JSON-safe values.
    """

    if value is None:
        return None

    # datetime/date objects are converted to ISO strings.
    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


# ================================================================
# PROJECT SERIALIZATION
# ================================================================

def serialize_project(project: Project) -> dict:
    """
    Convert a Project SQLAlchemy object into a dictionary.
    """

    return {
        "project_id": project.project_id,
        "mp_name": project.mp_name,
        "state": project.state,
        "district": project.district,
        "category": project.category,
        "work_description": project.work_description,

        "estimated_cost_lakh": clean_value(
            project.estimated_cost_lakh
        ),

        "sanctioned_amount_lakh": clean_value(
            project.sanctioned_amount_lakh
        ),

        "expenditure_lakh": clean_value(
            project.expenditure_lakh
        ),

        "physical_progress_pct": clean_value(
            project.physical_progress_pct
        ),

        "planned_duration_days": clean_value(
            project.planned_duration_days
        ),

        "elapsed_days": clean_value(
            project.elapsed_days
        ),

        "start_date": clean_value(
            project.start_date
        ),

        "expected_completion_date": clean_value(
            project.expected_completion_date
        ),

        "current_status": project.current_status,

        "latitude": clean_value(
            project.latitude
        ),

        "longitude": clean_value(
            project.longitude
        ),

        "implementing_agency": project.implementing_agency,

        "category_avg_expenditure_lakh": clean_value(
            project.category_avg_expenditure_lakh
        ),

        "category_std_expenditure_lakh": clean_value(
            project.category_std_expenditure_lakh
        ),
    }


# ================================================================
# RISK RESULT SERIALIZATION
# ================================================================

def serialize_risk_result(
    result: RiskResult | None,
) -> dict:
    """
    Convert a RiskResult object into a dictionary.
    """

    if result is None:
        return {
            "sanction_overrun_pct": None,
            "delay_pct": None,
            "max_similarity_pct": None,
            "similar_project_count": None,
            "duplicate_signal": None,

            "spending_zscore": None,
            "spending_anomaly": None,

            "cost_score": None,
            "delay_score": None,
            "duplicate_score": None,
            "spending_score": None,

            "risk_score": None,
            "risk_level": None,
            "risk_reasons": None,

            "isolation_prediction": None,
            "isolation_flag": None,
            "isolation_anomaly_score": None,
        }

    return {
        "sanction_overrun_pct": clean_value(
            result.sanction_overrun_pct
        ),

        "delay_pct": clean_value(
            result.delay_pct
        ),

        "max_similarity_pct": clean_value(
            result.max_similarity_pct
        ),

        "similar_project_count": clean_value(
            result.similar_project_count
        ),

        "duplicate_signal": clean_value(
            result.duplicate_signal
        ),

        "spending_zscore": clean_value(
            result.spending_zscore
        ),

        "spending_anomaly": clean_value(
            result.spending_anomaly
        ),

        "cost_score": clean_value(
            result.cost_score
        ),

        "delay_score": clean_value(
            result.delay_score
        ),

        "duplicate_score": clean_value(
            result.duplicate_score
        ),

        "spending_score": clean_value(
            result.spending_score
        ),

        "risk_score": clean_value(
            result.risk_score
        ),

        "risk_level": result.risk_level,

        "risk_reasons": result.risk_reasons,

        "isolation_prediction": clean_value(
            result.isolation_prediction
        ),

        "isolation_flag": clean_value(
            result.isolation_flag
        ),

        "isolation_anomaly_score": clean_value(
            result.isolation_anomaly_score
        ),
    }


# ================================================================
# SPENDING RESULT SERIALIZATION
# ================================================================

def serialize_spending_result(
    result: SpendingAnalysis | None,
) -> dict:
    """
    Convert a SpendingAnalysis object into a dictionary.
    """

    if result is None:
        return {
            "spending_zscore": None,
            "spending_anomaly": None,
        }

    return {
        "spending_zscore": clean_value(
            result.spending_zscore
        ),

        "spending_anomaly": clean_value(
            result.spending_anomaly
        ),
    }


# ================================================================
# GET ALL PROJECTS
# ================================================================

def get_all_projects() -> list[dict]:
    """
    Retrieve all project records and merge their analytical
    results into a single project-level dictionary.

    PostgreSQL is the primary source.
    """

    db = SessionLocal()

    try:
        # --------------------------------------------------------
        # Load projects
        # --------------------------------------------------------

        projects = (
            db.query(Project)
            .order_by(Project.project_id)
            .all()
        )

        # --------------------------------------------------------
        # Load risk results
        # --------------------------------------------------------

        risk_results = (
            db.query(RiskResult)
            .all()
        )

        risk_map = {
            str(result.project_id): result
            for result in risk_results
        }

        # --------------------------------------------------------
        # Load spending analysis
        # --------------------------------------------------------

        spending_results = (
            db.query(SpendingAnalysis)
            .all()
        )

        spending_map = {
            str(result.project_id): result
            for result in spending_results
        }

        # --------------------------------------------------------
        # Merge everything
        # --------------------------------------------------------

        records = []

        for project in projects:

            project_id = str(
                project.project_id
            )

            record = {}

            # Base project information
            record.update(
                serialize_project(project)
            )

            # Risk analysis
            risk_result = risk_map.get(
                project_id
            )

            record.update(
                serialize_risk_result(
                    risk_result
                )
            )

            # Spending analysis
            spending_result = spending_map.get(
                project_id
            )

            record.update(
                serialize_spending_result(
                    spending_result
                )
            )

            records.append(record)

        return records

    finally:
        db.close()


# ================================================================
# GET SINGLE PROJECT
# ================================================================

def get_project_by_id(
    project_id: str,
) -> dict | None:
    """
    Retrieve one project and its analytical results.
    """

    target_id = str(
        project_id
    ).strip().upper()

    db = SessionLocal()

    try:

        project = (
            db.query(Project)
            .filter(
                Project.project_id == target_id
            )
            .first()
        )

        if project is None:
            return None

        risk_result = (
            db.query(RiskResult)
            .filter(
                RiskResult.project_id == target_id
            )
            .first()
        )

        spending_result = (
            db.query(SpendingAnalysis)
            .filter(
                SpendingAnalysis.project_id == target_id
            )
            .first()
        )

        record = {}

        record.update(
            serialize_project(project)
        )

        record.update(
            serialize_risk_result(
                risk_result
            )
        )

        record.update(
            serialize_spending_result(
                spending_result
            )
        )

        return record

    finally:
        db.close()


# ================================================================
# DATABASE SUMMARY
# ================================================================

def get_database_summary() -> dict:
    """
    Return basic PostgreSQL record counts.
    """

    db = SessionLocal()

    try:

        project_count = (
            db.query(Project)
            .count()
        )

        risk_count = (
            db.query(RiskResult)
            .count()
        )

        spending_count = (
            db.query(SpendingAnalysis)
            .count()
        )

        return {
            "projects": project_count,
            "risk_results": risk_count,
            "spending_analysis": spending_count,
        }

    finally:
        db.close()