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
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np

# Ensure project root/code is in path for imports
# File is at code/analysis/threshold_identification_t004.py
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "code") not in sys.path:
    sys.path.insert(0, str(ROOT / "code"))

from utils.config import get_project_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

METHOD = "empirical_50pct_crossing"
PROB_THRESHOLD = 0.5


def identify_thresholds(csv_path: Path) -> Tuple[List[Dict[str, Any]], Optional[float]]:
    """
    Processes the validated sweep results to find the 50% crossing point for theta.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {csv_path}. Ensure T003 has completed successfully."
        )

    df = pd.read_csv(csv_path)
    
    # Required columns check
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
    # Identify all unique configuration groups
    group_keys = (
        df[["N", "k", "pattern_type"]]
        .drop_duplicates()
        .sort_values(["N", "k", "pattern_type"])
    )

    for _, gk in group_keys.iterrows():
        # Filter data for this specific group
        sub = df[
            (df["N"] == gk["N"])
            & (df["k"] == gk["k"])
            & (df["pattern_type"] == gk["pattern_type"])
        ]
        
        # Sort the swept theta values
        thetas = sorted(sub["theta"].unique())
        theta_c = None
        
        for theta in thetas:
            # Calculate the outlier probability for this theta
            tsub = sub[sub["theta"] == theta]
            prob = float(tsub["outlier_flag"].mean())
            
            # Find the smallest theta where prob >= 0.5
            if prob >= PROB_THRESHOLD:
                theta_c = float(theta)
                break
        
        groups.append(
            {
                "N": int(gk["N"]),
                "k": int(gk["k"]),
                "pattern_type": str(gk["pattern_type"]),
                "theta_c_empirical": theta_c,
                "method": METHOD,
            }
        )

    # Overall threshold: median of the identified thresholds across all groups
    observed = [g["theta_c_empirical"] for g in groups if g["theta_c_empirical"] is not None]
    overall = float(np.median(observed)) if observed else None
    
    return groups, overall


def main() -> int:
    """
    Main entry point for Task T004.
    """
    paths = get_project_paths()
    csv_path = paths["processed"] / "validated_sweep_results.csv"
    out_path = paths["processed"] / "threshold_identification.json"

    log.info(f"Starting T004: Identifying empirical thresholds from {csv_path}")
    
    try:
        groups, overall = identify_thresholds(csv_path)
        
        result = {
            "groups": groups,
            "overall_theta_c": overall,
        }
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        log.info(f"Successfully wrote threshold identification to {out_path}")
        log.info(f"Processed {len(groups)} groups. Overall theta_c: {overall}")
        return 0
    except Exception as e:
        log.exception(f"Failed to identify thresholds: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())