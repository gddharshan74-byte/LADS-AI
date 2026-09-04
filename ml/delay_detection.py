import pandas as pd


DATA_PATH = "backend/data/mplads_demo_expanded.csv"


def detect_delay_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect potential execution delays by comparing
    elapsed project time with planned duration.

    This is an early-warning signal, not a determination
    of wrongdoing.
    """

    df["delay_days"] = (
        df["elapsed_days"] - df["planned_duration_days"]
    )

    df["delay_pct"] = (
        df["delay_days"]
        / df["planned_duration_days"]
    ) * 100

    # Prototype rule:
    # Flag projects that have exceeded their planned duration
    # by more than 20%, or are explicitly marked as delayed.
    df["delay_anomaly"] = (
        (df["delay_pct"] > 20)
        | (df["current_status"].str.lower() == "delayed")
    )

    return df


def main():
    df = pd.read_csv(DATA_PATH)

    result = detect_delay_anomalies(df)

    print("\nLADS AI — DELAY DETECTION")
    print("=" * 70)

    columns = [
        "project_id",
        "current_status",
        "planned_duration_days",
        "elapsed_days",
        "delay_days",
        "delay_pct",
        "delay_anomaly",
    ]

    print(
        result[columns]
        .round(2)
        .to_string(index=False)
    )

    print("\nPotential Execution Delays")
    print("=" * 70)

    anomalies = result[result["delay_anomaly"]]

    if anomalies.empty:
        print("No potential execution delays detected.")
    else:
        for _, row in anomalies.iterrows():
            print(
                f"{row['project_id']} | "
                f"Status: {row['current_status']} | "
                f"Delay: {row['delay_days']:.0f} days | "
                f"Delay: {row['delay_pct']:.1f}%"
            )


if __name__ == "__main__":
    main()