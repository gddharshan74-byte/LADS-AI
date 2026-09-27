"""
PRISM AI - MPLADS Database Synchronization

Flow:
    Source
      ↓
    mplads_source.py
      ↓
    mplads_transformer.py
      ↓
    PostgreSQL projects table
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------
# PRISM AI imports
# ---------------------------------------------------------------

from backend.database import SessionLocal
from backend.models.database_models import Project

from backend.ingestion.mplads_source import (
    load_source,
    get_source_summary,
)

from backend.ingestion.mplads_transformer import (
    transform,
)


# ---------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------

def get_existing_projects(session):
    """Return existing project IDs from PostgreSQL."""

    rows = (
        session.query(Project.project_id)
        .all()
    )

    return {
        row[0]
        for row in rows
        if row[0]
    }


def upsert_projects(session, records):
    """
    Insert new projects and update existing projects.

    project_id is treated as the logical identifier.
    """

    existing = {
        row.project_id: row
        for row in session.query(Project).all()
    }

    inserted = 0
    updated = 0

    for record in records:

        project_id = record.get("project_id")

        if not project_id:
            continue

        if project_id in existing:

            project = existing[project_id]

            for key, value in record.items():

                if hasattr(project, key):
                    setattr(
                        project,
                        key,
                        value
                    )

            updated += 1

        else:

            project = Project(
                **{
                    key: value
                    for key, value in record.items()
                    if hasattr(Project, key)
                }
            )

            session.add(project)

            inserted += 1

    session.commit()

    return inserted, updated


# ---------------------------------------------------------------
# Main synchronization logic
# ---------------------------------------------------------------

def sync_source(
    source: str,
    write: bool = False,
):
    """
    Load source, transform it and optionally synchronize
    the PostgreSQL projects table.
    """

    print("\n======================================")
    print(" PRISM AI - MPLADS SOURCE SYNC")
    print("======================================")

    # -----------------------------------------------------------
    # 1. Load source
    # -----------------------------------------------------------

    df = load_source(source)

    summary = get_source_summary(df)

    print("\n[1] SOURCE SUMMARY")
    print("------------------")

    for key, value in summary.items():
        print(f"{key}: {value}")

    # -----------------------------------------------------------
    # 2. Transform
    # -----------------------------------------------------------

    print("\n[2] TRANSFORMING SOURCE")

    transformed = transform(df)

    print(
        f"[PRISM AI] Transformed records: "
        f"{len(transformed)}"
    )

    # -----------------------------------------------------------
    # 3. PostgreSQL comparison
    # -----------------------------------------------------------

    session = SessionLocal()

    try:

        existing_ids = get_existing_projects(
            session
        )

        incoming_ids = {
            record.get("project_id")
            for record in transformed
            if record.get("project_id")
        }

        new_ids = incoming_ids - existing_ids
        existing_incoming_ids = (
            incoming_ids & existing_ids
        )

        print("\n[3] DATABASE COMPARISON")
        print("-----------------------")
        print(
            f"Existing projects in DB : "
            f"{len(existing_ids)}"
        )
        print(
            f"Incoming projects        : "
            f"{len(incoming_ids)}"
        )
        print(
            f"New projects             : "
            f"{len(new_ids)}"
        )
        print(
            f"Existing to update       : "
            f"{len(existing_incoming_ids)}"
        )

        # -------------------------------------------------------
        # 4. Dry run
        # -------------------------------------------------------

        if not write:

            print(
                "\n[DRY RUN] No database changes made."
            )

            return {
                "source_records": len(df),
                "transformed_records": len(transformed),
                "new_projects": len(new_ids),
                "updated_projects": len(
                    existing_incoming_ids
                ),
                "written": False,
            }

        # -------------------------------------------------------
        # 5. Write to PostgreSQL
        # -------------------------------------------------------

        print(
            "\n[4] WRITING TO POSTGRESQL"
        )

        inserted, updated = upsert_projects(
            session,
            transformed,
        )

        print(
            f"Inserted: {inserted}"
        )

        print(
            f"Updated : {updated}"
        )

        print(
            "\n[PRISM AI] Database synchronization "
            "completed successfully."
        )

        return {
            "source_records": len(df),
            "transformed_records": len(transformed),
            "new_projects": inserted,
            "updated_projects": updated,
            "written": True,
        }

    except Exception:

        session.rollback()
        raise

    finally:

        session.close()


# ---------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "PRISM AI MPLADS source-to-PostgreSQL sync"
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        help=(
            "CSV, Excel, JSON file path or HTTP/HTTPS URL"
        ),
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Actually write/update PostgreSQL. "
            "Without this flag the command performs a dry run."
        ),
    )

    args = parser.parse_args()

    try:

        result = sync_source(
            source=args.source,
            write=args.write,
        )

        print("\n======================================")
        print(" SYNC RESULT")
        print("======================================")

        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as exc:

        print(
            "\n[PRISM AI] Synchronization failed:"
        )

        print(exc)

        raise SystemExit(1)


if __name__ == "__main__":
    main()