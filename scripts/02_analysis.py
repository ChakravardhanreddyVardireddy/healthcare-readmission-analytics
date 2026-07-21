"""
02_analysis.py

Runs the core descriptive analysis on the cleaned CMS HRRP sample and
prints the key findings used in README.md. This is the "business analysis"
layer on top of the cleaned data produced by 01_clean_data.py.

Usage
-----
python scripts/02_analysis.py
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    df = pd.read_csv(DATA_DIR / "hrrp_clean.csv")
    valid = df.dropna(subset=["excess_readmission_ratio"])

    print("=" * 60)
    print("OVERALL")
    print("=" * 60)
    total = len(valid)
    penalized = (valid["excess_readmission_ratio"] > 1.0).sum()
    print(f"Facility-measure records with a scored ratio: {total}")
    print(f"Records with excess readmissions (ratio > 1.0): {penalized} "
          f"({penalized / total * 100:.1f}%)")

    print("\n" + "=" * 60)
    print("BY CONDITION (measure)")
    print("=" * 60)
    by_measure = valid.groupby("measure_name").agg(
        avg_excess_ratio=("excess_readmission_ratio", "mean"),
        n_hospitals=("excess_readmission_ratio", "count"),
    )
    by_measure["pct_penalized"] = valid.groupby("measure_name")[
        "excess_readmission_ratio"
    ].apply(lambda s: (s > 1.0).mean() * 100)
    print(by_measure.sort_values("avg_excess_ratio", ascending=False).round(3))

    print("\n" + "=" * 60)
    print("BY STATE")
    print("=" * 60)
    by_state = valid.groupby("state").agg(
        avg_excess_ratio=("excess_readmission_ratio", "mean"),
        n_hospitals=("excess_readmission_ratio", "count"),
    )
    by_state["pct_penalized"] = valid.groupby("state")[
        "excess_readmission_ratio"
    ].apply(lambda s: (s > 1.0).mean() * 100)
    print(by_state.sort_values("avg_excess_ratio", ascending=False).round(3))

    print("\n" + "=" * 60)
    print("TOP 5 WORST-PERFORMING FACILITY-MEASURES")
    print("=" * 60)
    worst = valid.nlargest(5, "excess_readmission_ratio")[
        ["facility_name", "state", "measure_name", "excess_readmission_ratio"]
    ]
    print(worst.to_string(index=False))

    print("\n" + "=" * 60)
    print("READMISSION RATE GAP (predicted - expected), avg by condition")
    print("=" * 60)
    gap_df = df.dropna(subset=["predicted_readmission_rate", "expected_readmission_rate"]).copy()
    gap_df["gap"] = gap_df["predicted_readmission_rate"] - gap_df["expected_readmission_rate"]
    print(gap_df.groupby("measure_name")["gap"].mean().sort_values(ascending=False).round(3))


if __name__ == "__main__":
    main()
