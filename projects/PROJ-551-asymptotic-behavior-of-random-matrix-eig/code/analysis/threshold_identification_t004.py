"""
Task T004: Identify the empirical critical threshold theta_c_empirical for each
configuration group (N, k, pattern_type) from the validated sweep results.

Method: empirical 50% crossing — for each group, select the SMALLEST swept theta
at which the outlier probability (fraction of runs with outlier_flag=True) is >= 0.5.

Reads:  data/processed/validated_sweep_results.csv (T003 output)
Writes: data/processed/threshold_identification.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_project_paths

METHOD = "empirical_50pct_crossing"
PROB_THRESHOLD = 0.5


def identify_thresholds(csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {csv_path}. Ensure T003 has completed."
        )
    df = pd.read_csv(csv_path)
    required = {"N", "k", "pattern_type", "theta", "outlier_flag"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns {sorted(missing)} in {csv_path}")

    # Normalize outlier_flag to boolean
    if df["outlier_flag"].dtype == object:
        df["outlier_flag"] = df["outlier_flag"].astype(str).str.lower().isin(
            ["true", "1", "yes"]
        )
    else:
        df["outlier_flag"] = df["outlier_flag"].astype(bool)

    groups = []
    group_keys = (
        df[["N", "k", "pattern_type"]].drop_duplicates().sort_values(["N", "k", "pattern_type"])
    )
    for _, gk in group_keys.iterrows():
        sub = df[
            (df["N"] == gk["N"])
            & (df["k"] == gk["k"])
            & (df["pattern_type"] == gk["pattern_type"])
        ]
        thetas = sorted(sub["theta"].unique())
        theta_c = None
        curve = []
        for theta in thetas:
            tsub = sub[sub["theta"] == theta]
            prob = float(tsub["outlier_flag"].mean())
            curve.append({"theta": float(theta), "outlier_probability": prob,
                          "num_runs": int(len(tsub))})
            if prob >= PROB_THRESHOLD and theta_c is None:
                theta_c = float(theta)
        groups.append(
            {
                "N": int(gk["N"]),
                "k": int(gk["k"]),
                "pattern_type": str(gk["pattern_type"]),
                "theta_c_empirical": theta_c,
                "method": METHOD,
                "outlier_probability_curve": curve,
            }
        )

    # Overall threshold: median over groups where a crossing was observed
    observed = [g["theta_c_empirical"] for g in groups if g["theta_c_empirical"] is not None]
    overall = float(pd.Series(observed).median()) if observed else None
    return groups, overall


def main() -> int:
    paths = get_project_paths()
    csv_path = paths["processed"] / "validated_sweep_results.csv"
    out_path = paths["processed"] / "threshold_identification.json"

    groups, overall = identify_thresholds(csv_path)

    result = {
        "method": METHOD,
        "probability_threshold": PROB_THRESHOLD,
        "description": (
            "Smallest swept theta at which the outlier probability "
            "(fraction of runs with outlier_flag=True) reaches >= 0.5, "
            "per configuration group (N, k, pattern_type)."
        ),
        "groups": groups,
        "overall_theta_c": overall,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    n_groups = len(groups)
    n_observed = sum(1 for g in groups if g["theta_c_empirical"] is not None)
    print(f"Wrote {out_path}")
    print(f"Groups: {n_groups} (crossing observed in {n_observed})")
    print(f"Overall theta_c (median): {overall}")
    for g in groups:
        print(
            f"  N={g['N']} k={g['k']} {g['pattern_type']}: "
            f"theta_c_empirical={g['theta_c_empirical']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())