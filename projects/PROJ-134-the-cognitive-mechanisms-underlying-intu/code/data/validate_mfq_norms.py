"""
T075-Validate: Validate real MFQ data against Gervais norms.

This script reads the real MFQ dataset (data/raw/mfq_real.csv) and performs
a Kolmogorov-Smirnov (KS) test against the psychometric norms defined in
data/config/gervais_norms.yaml.

It strictly enforces the "Real Data Only" constraint: if the input file
is missing or the data source is unreachable, it raises an error.
It does NOT generate synthetic data.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_path
from code.utils.logging import log_operation, ReproducibilityLogger

# Constants
MFQ_REAL_PATH = get_path("data", "raw/mfq_real.csv")
NORMS_PATH = get_path("data", "config/gervais_norms.yaml")
OUTPUT_PATH = get_path("data", "logs", "mfq_norm_validation.json")

# Dimensions to validate
MFQ_DIMENSIONS = ["care", "fairness", "loyalty", "authority", "purity"]


def load_norms(norms_path: Path) -> Dict[str, Dict[str, float]]:
    """Load Gervais et al. psychometric norms from YAML."""
    import yaml

    if not norms_path.exists():
        raise FileNotFoundError(f"Norms file not found at {norms_path}. "
                                "Ensure T007b (gervais_norms.yaml) is complete.")

    with open(norms_path, "r") as f:
        data = yaml.safe_load(f)

    # Validate structure
    for dim in MFQ_DIMENSIONS:
        if dim not in data:
            raise ValueError(f"Missing dimension '{dim}' in norms file.")
        if "mean" not in data[dim] or "std" not in data[dim]:
            raise ValueError(f"Dimension '{dim}' missing 'mean' or 'std' in norms file.")

    return data


def load_real_mfq_data(mfq_path: Path) -> pd.DataFrame:
    """Load real MFQ data. Fails loudly if missing."""
    if not mfq_path.exists():
        raise FileNotFoundError(
            f"Real MFQ data not found at {mfq_path}. "
            "Ensure T054b (fetch_real.py) has completed successfully and generated "
            "data/raw/mfq_real.csv. Do not proceed with simulation fallback."
        )

    df = pd.read_csv(mfq_path)

    # Validate expected columns exist
    missing_cols = [col for col in MFQ_DIMENSIONS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Real MFQ data missing required columns: {missing_cols}. "
            f"Expected columns: {MFQ_DIMENSIONS}"
        )

    return df


def perform_ks_test(data: pd.DataFrame, norms: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test for each dimension against the normal distribution
    defined by the norms.

    Returns a dictionary of results.
    """
    results = {}

    for dim in MFQ_DIMENSIONS:
        # Extract observed data
        observed = data[dim].dropna().values

        if len(observed) == 0:
            results[dim] = {
                "status": "error",
                "message": "No data points available for this dimension."
            }
            continue

        # Define theoretical distribution from norms
        mean = norms[dim]["mean"]
        std = norms[dim]["std"]

        # Perform KS test against the theoretical CDF
        # Note: scipy.stats.kstest can accept a CDF function or a distribution name + params
        # We use the norm.cdf with loc and scale
        statistic, p_value = stats.kstest(observed, 'norm', args=(mean, std))

        # Determine pass/fail based on p-value threshold (alpha = 0.05)
        # Null hypothesis: data comes from the distribution
        # p > 0.05 => Fail to reject null => Data is consistent with norms (PASS)
        is_consistent = p_value > 0.05

        results[dim] = {
            "mean_observed": float(np.mean(observed)),
            "std_observed": float(np.std(observed)),
            "mean_expected": mean,
            "std_expected": std,
            "ks_statistic": float(statistic),
            "p_value": float(p_value),
            "is_consistent": is_consistent,
            "status": "PASS" if is_consistent else "FAIL"
        }

    return results


def write_report(results: Dict[str, Any], output_path: Path) -> None:
    """Write validation report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "validation_type": "KS-test against Gervais norms",
        "input_file": str(MFQ_REAL_PATH),
        "norms_file": str(NORMS_PATH),
        "results": results,
        "overall_status": "PASS" if all(r.get("status") == "PASS" for r in results.values()) else "FAIL"
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    log_operation("validation_complete", output=str(output_path), status=report["overall_status"])
    print(f"Validation report written to {output_path}")


def main() -> None:
    """Main entry point for T075-Validate."""
    logger = ReproducibilityLogger(name="mfq_validation")
    log_operation("start_validation", task_id="T075")

    try:
        # 1. Load Norms
        logger.log("loading_norms", path=str(NORMS_PATH))
        norms = load_norms(NORMS_PATH)

        # 2. Load Real Data (Fails loudly if missing)
        logger.log("loading_real_data", path=str(MFQ_REAL_PATH))
        df = load_real_mfq_data(MFQ_REAL_PATH)
        print(f"Loaded {len(df)} rows from real MFQ data.")

        # 3. Perform Validation
        logger.log("performing_ks_test")
        results = perform_ks_test(df, norms)

        # 4. Write Report
        logger.log("writing_report", path=str(OUTPUT_PATH))
        write_report(results, OUTPUT_PATH)

        # Summary output
        print("\n--- Validation Summary ---")
        for dim, res in results.items():
            print(f"{dim}: {res['status']} (p={res['p_value']:.4f})")
        print(f"Overall: {results}")

    except FileNotFoundError as e:
        logger.log("error", type="FileNotFoundError", message=str(e))
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.log("error", type="ValueError", message=str(e))
        print(f"VALIDATION ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.log("error", type="Unexpected", message=str(e))
        print(f"UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    main()