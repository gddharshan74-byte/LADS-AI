import pandas as pd


DATA_PATH = "backend/data/mplads_demo_expanded.csv"


def detect_cost_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect potential cost anomalies using:
    1. Expenditure vs sanctioned amount
    2. Expenditure vs estimated cost

    This is an early-warning signal, not a fraud determination.
    """

    # Cost overrun compared with sanctioned amount
    df["sanction_overrun_pct"] = (
        (df["expenditure_lakh"] - df["sanctioned_amount_lakh"])
        / df["sanctioned_amount_lakh"]
    ) * 100

    # Difference between expenditure and estimated cost
    df["estimate_deviation_pct"] = (
        (df["expenditure_lakh"] - df["estimated_cost_lakh"])
        / df["estimated_cost_lakh"]
    ) * 100

    # Configurable early-warning thresholds
    df["cost_anomaly"] = (
        (df["sanction_overrun_pct"] > 20)
        | (df["estimate_deviation_pct"] > 25)
    )

    return df


def main():
    df = pd.read_csv(DATA_PATH)

    result = detect_cost_anomalies(df)

    print("\nLADS AI — COST ANOMALY DETECTION")
    print("=" * 70)

    columns = [
        "project_id",
        "category",
        "estimated_cost_lakh",
        "sanctioned_amount_lakh",
        "expenditure_lakh",
        "sanction_overrun_pct",
        "estimate_deviation_pct",
        "cost_anomaly",
    ]

    print(
        result[columns]
        .round(2)
        .to_string(index=False)
    )

    print("\nPotential Cost Anomalies")
    print("=" * 70)

    anomalies = result[result["cost_anomaly"]]

    if anomalies.empty:
        print("No potential cost anomalies detected.")
    else:
        for _, row in anomalies.iterrows():
            print(
                f"{row['project_id']} | "
                f"{row['category']} | "
                f"Expenditure: ₹{row['expenditure_lakh']:.2f}L | "
                f"Sanction overrun: {row['sanction_overrun_pct']:.1f}% | "
                f"Estimate deviation: {row['estimate_deviation_pct']:.1f}%"
            )


if __name__ == "__main__":
    main()