from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "backend" / "data" / "mplads_demo.csv"


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    print("LADS AI — Dataset Check")
    print("=" * 30)
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print("\nColumns:")
    for column in df.columns:
        print(f"- {column}")

    print("\nFirst 5 records:")
    print(df.head().to_string(index=False))

    numeric = [
        "estimated_cost_lakh",
        "sanctioned_amount_lakh",
        "expenditure_lakh",
        "physical_progress_pct",
        "planned_duration_days",
        "elapsed_days",
    ]
    print("\nBasic checks:")
    print(df[numeric].describe().round(2).to_string())


if __name__ == "__main__":
    main()
