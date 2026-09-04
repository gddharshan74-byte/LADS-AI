import pandas as pd


DATA_PATH = "backend/data/mplads_demo_expanded.csv"
OUTPUT_PATH = "backend/data/spending_results.csv"

# Prototype threshold.
# This is NOT an official MPLADS threshold.
ZSCORE_THRESHOLD = 2.0


def detect_spending_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect unusually high expenditure compared with projects
    in the same category.

    A project is flagged when its expenditure is at least
    2 standard deviations above the category mean.
    """

    category_mean = df.groupby("category")["expenditure_lakh"].transform(
        "mean"
    )

    category_std = df.groupby("category")["expenditure_lakh"].transform(
        "std"
    )

    df["category_avg_expenditure_lakh"] = category_mean
    df["category_std_expenditure_lakh"] = category_std

    # Avoid division-by-zero for categories with no variation.
    df["spending_zscore"] = (
        (df["expenditure_lakh"] - df["category_avg_expenditure_lakh"])
        / df["category_std_expenditure_lakh"].replace(0, pd.NA)
    )

    df["spending_anomaly"] = (
        df["spending_zscore"] >= ZSCORE_THRESHOLD
    ).fillna(False)

    return df


def main():
    df = pd.read_csv(DATA_PATH)

    result = detect_spending_anomalies(df)

    print("\nLADS AI — SPENDING PATTERN ANALYSIS")
    print("=" * 80)

    print(f"Projects analyzed: {len(result)}")
    print(f"Z-score threshold: {ZSCORE_THRESHOLD}")

    columns = [
        "project_id",
        "category",
        "expenditure_lakh",
        "category_avg_expenditure_lakh",
        "category_std_expenditure_lakh",
        "spending_zscore",
        "spending_anomaly",
    ]

    print("\nSpending Analysis")
    print("=" * 80)

    print(
        result[columns]
        .sort_values("spending_zscore", ascending=False)
        .head(20)
        .round(2)
        .to_string(index=False)
    )

    anomalies = result[result["spending_anomaly"]].copy()

    print("\nPotential Spending Pattern Anomalies")
    print("=" * 80)

    if anomalies.empty:
        print("No unusual spending patterns detected.")
    else:
        for _, row in anomalies.iterrows():
            print(
                f"{row['project_id']} | "
                f"{row['category']} | "
                f"Expenditure: ₹{row['expenditure_lakh']:.2f}L | "
                f"Category average: "
                f"₹{row['category_avg_expenditure_lakh']:.2f}L | "
                f"Z-score: {row['spending_zscore']:.2f}"
            )

    result.to_csv(OUTPUT_PATH, index=False)

    print("\nOutput file created:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()