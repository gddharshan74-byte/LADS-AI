"""
PRISM AI - SQLAlchemy Database Models

These models represent the PostgreSQL schema used by PRISM AI.

Tables:
    projects
    risk_results
    spending_analysis
    duplicate_signals

Note:
    The current implementation uses the common project_id field
    as a logical link between tables. Explicit SQLAlchemy ForeignKey
    constraints are intentionally not added here so the existing
    database schema remains unchanged.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    Integer,
    String,
    Text,
)

# IMPORTANT:
# Because FastAPI is launched as:
#
#     python -m uvicorn backend.main:app
#
# the database module must be imported through the backend package.
from backend.database import Base


# ================================================================
# PROJECTS
# ================================================================

class Project(Base):
    """
    Core MPLADS project information.
    """

    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    mp_name = Column(
        String(255),
        nullable=True,
    )

    state = Column(
        String(255),
        nullable=True,
    )

    district = Column(
        String(255),
        nullable=True,
    )

    category = Column(
        String(255),
        nullable=True,
    )

    work_description = Column(
        Text,
        nullable=True,
    )

    estimated_cost_lakh = Column(
        Float,
        nullable=True,
    )

    sanctioned_amount_lakh = Column(
        Float,
        nullable=True,
    )

    expenditure_lakh = Column(
        Float,
        nullable=True,
    )

    physical_progress_pct = Column(
        Float,
        nullable=True,
    )

    planned_duration_days = Column(
        Integer,
        nullable=True,
    )

    elapsed_days = Column(
        Integer,
        nullable=True,
    )

    start_date = Column(
        Date,
        nullable=True,
    )

    expected_completion_date = Column(
        Date,
        nullable=True,
    )

    current_status = Column(
        String(100),
        nullable=True,
    )

    latitude = Column(
        Float,
        nullable=True,
    )

    longitude = Column(
        Float,
        nullable=True,
    )

    implementing_agency = Column(
        String(255),
        nullable=True,
    )

    category_avg_expenditure_lakh = Column(
        Float,
        nullable=True,
    )

    category_std_expenditure_lakh = Column(
        Float,
        nullable=True,
    )


# ================================================================
# RISK RESULTS
# ================================================================

class RiskResult(Base):
    """
    Project-level rule-based and machine-learning risk results.
    """

    __tablename__ = "risk_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        String(100),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------
    # Individual risk signals
    # ------------------------------------------------------------

    sanction_overrun_pct = Column(
        Float,
        nullable=True,
    )

    delay_pct = Column(
        Float,
        nullable=True,
    )

    max_similarity_pct = Column(
        Float,
        nullable=True,
    )

    similar_project_count = Column(
        Integer,
        nullable=True,
    )

    duplicate_signal = Column(
        Boolean,
        nullable=True,
    )

    spending_zscore = Column(
        Float,
        nullable=True,
    )

    spending_anomaly = Column(
        Boolean,
        nullable=True,
    )

    # ------------------------------------------------------------
    # Component scores
    # ------------------------------------------------------------

    cost_score = Column(
        Float,
        nullable=True,
    )

    delay_score = Column(
        Float,
        nullable=True,
    )

    duplicate_score = Column(
        Float,
        nullable=True,
    )

    spending_score = Column(
        Float,
        nullable=True,
    )

    # ------------------------------------------------------------
    # Unified risk result
    # ------------------------------------------------------------

    risk_score = Column(
        Float,
        nullable=True,
    )

    risk_level = Column(
        String(50),
        nullable=True,
    )

    risk_reasons = Column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------
    # Isolation Forest
    # ------------------------------------------------------------

    isolation_prediction = Column(
        Integer,
        nullable=True,
    )

    isolation_flag = Column(
        Boolean,
        nullable=True,
    )

    isolation_anomaly_score = Column(
        Float,
        nullable=True,
    )


# ================================================================
# DUPLICATE SIGNALS
# ================================================================

class DuplicateSignal(Base):
    """
    Project-level NLP similarity / duplicate signals.
    """

    __tablename__ = "duplicate_signals"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        String(100),
        nullable=False,
        index=True,
    )

    max_similarity_pct = Column(
        Float,
        nullable=True,
    )

    similar_project_count = Column(
        Integer,
        nullable=True,
    )

    duplicate_signal = Column(
        Boolean,
        nullable=True,
    )


# ================================================================
# SPENDING ANALYSIS
# ================================================================

class SpendingAnalysis(Base):
    """
    Category-relative expenditure analysis.
    """

    __tablename__ = "spending_analysis"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        String(100),
        nullable=False,
        index=True,
    )

    spending_zscore = Column(
        Float,
        nullable=True,
    )

    spending_anomaly = Column(
        Boolean,
        nullable=True,
    )