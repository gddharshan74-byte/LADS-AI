import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    MetaData,
    Table,
    create_engine,
    text,
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

LOCAL_DATABASE_URL = os.getenv("DATABASE_URL")
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

if not LOCAL_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from the root .env file."
    )

if not NEON_DATABASE_URL:
    raise RuntimeError(
        "NEON_DATABASE_URL is missing from the root .env file."
    )


# ============================================================
# DATABASE ENGINES
# ============================================================

local_engine = create_engine(
    LOCAL_DATABASE_URL,
    pool_pre_ping=True,
)

neon_engine = create_engine(
    NEON_DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# TABLES TO MIGRATE
# ============================================================

TABLE_NAMES = [
    "projects",
    "risk_results",
    "spending_analysis",
    "duplicate_signals",
]


# ============================================================
# BUILD TABLE DEFINITION FOR NEON
# ============================================================

def build_neon_table(local_table: Table, neon_metadata: MetaData) -> Table:
    """
    Re-create a reflected local PostgreSQL table for Neon.

    We copy:
        - column names
        - column types
        - primary-key flags
        - nullability

    We intentionally do not copy local server defaults/sequences,
    because those may reference objects that exist only in the
    local PostgreSQL database.
    """

    columns = []

    for source_column in local_table.columns:
        columns.append(
            Column(
                source_column.name,
                source_column.type,
                primary_key=source_column.primary_key,
                nullable=source_column.nullable,
            )
        )

    return Table(
        local_table.name,
        neon_metadata,
        *columns,
    )


# ============================================================
# MIGRATION
# ============================================================

def migrate_table(table_name: str) -> tuple[int, int]:
    """
    Copy one table from local PostgreSQL to Neon.

    Returns:
        (source_count, destination_count)
    """

    print()
    print("=" * 70)
    print(f"MIGRATING TABLE: {table_name}")
    print("=" * 70)

    # --------------------------------------------------------
    # Reflect local table
    # --------------------------------------------------------

    local_metadata = MetaData()

    local_table = Table(
        table_name,
        local_metadata,
        autoload_with=local_engine,
    )

    # --------------------------------------------------------
    # Read local rows
    # --------------------------------------------------------

    with local_engine.connect() as local_connection:
        rows = local_connection.execute(
            local_table.select()
        ).mappings().all()

    source_count = len(rows)

    print(f"Local rows: {source_count}")

    # --------------------------------------------------------
    # Create destination table
    # --------------------------------------------------------

    neon_metadata = MetaData()

    neon_table = build_neon_table(
        local_table,
        neon_metadata,
    )

    neon_metadata.create_all(
        neon_engine,
        checkfirst=True,
    )

    # --------------------------------------------------------
    # Replace destination data
    # --------------------------------------------------------

    with neon_engine.begin() as neon_connection:

        # Clear existing rows if the table already exists.
        neon_connection.execute(
            neon_table.delete()
        )

        if rows:
            neon_connection.execute(
                neon_table.insert(),
                [dict(row) for row in rows],
            )

    # --------------------------------------------------------
    # Verify destination count
    # --------------------------------------------------------

    with neon_engine.connect() as neon_connection:
        destination_count = neon_connection.execute(
            text(
                f'SELECT COUNT(*) FROM "{table_name}"'
            )
        ).scalar_one()

    print(f"Neon rows:  {destination_count}")

    if source_count != destination_count:
        raise RuntimeError(
            f"Row-count mismatch for {table_name}: "
            f"local={source_count}, neon={destination_count}"
        )

    print("Migration successful.")

    return source_count, destination_count


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 70)
    print("              PRISM AI → NEON DATABASE MIGRATION")
    print("=" * 70)

    print()
    print("Local PostgreSQL connection: FOUND")
    print("Neon PostgreSQL connection : FOUND")

    # --------------------------------------------------------
    # Verify both connections
    # --------------------------------------------------------

    with local_engine.connect() as connection:
        local_info = connection.execute(
            text(
                "SELECT current_database(), current_user"
            )
        ).fetchone()

    with neon_engine.connect() as connection:
        neon_info = connection.execute(
            text(
                "SELECT current_database(), current_user"
            )
        ).fetchone()

    print()
    print(f"Local database: {local_info}")
    print(f"Neon database : {neon_info}")

    # --------------------------------------------------------
    # Migrate tables
    # --------------------------------------------------------

    totals = []

    for table_name in TABLE_NAMES:
        totals.append(
            migrate_table(table_name)
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("              MIGRATION COMPLETE")
    print("=" * 70)

    for table_name, (source_count, destination_count) in zip(
        TABLE_NAMES,
        totals,
    ):
        print(
            f"{table_name:<22} "
            f"local={source_count:<5} "
            f"neon={destination_count:<5}"
        )

    print()
    print("PRISM AI data has been copied to Neon successfully.")


if __name__ == "__main__":
    main()