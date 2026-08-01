"""
T025 Implementation: Generate statistical_results.json

Reads binned energy data from data/derived/energy_samples.csv,
executes the statistical tests defined in code/stats.py (KS and Chi-squared),
applies Benjamini-Hochberg correction, and writes the final results to
artifacts/statistical_results.json.

This script assumes T017 (energy_samples.csv) and T021-T024 (stats.py functions)
are complete.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import numpy as np

# Import the specific functions from the stats module as defined in the API surface
from stats import (
    StatsError,
    bin_energy_data,
    perform_ks_test,
    perform_chisquared_test,
    apply_benjamini_hochberg,
    run_statistical_analysis
)

def main():
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "derived" / "energy_samples.csv"
    output_path = project_root / "artifacts" / "statistical_results.json"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T017 (energy_samples.csv generation) is complete."
        )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading energy data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise StatsError(f"Failed to load energy data: {e}")

    # Validate expected columns
    required_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise StatsError(f"Missing required columns in input data: {missing_cols}")

    print(f"Loaded {len(df)} samples. Binning data by frequency and material...")

    # Run the full statistical analysis pipeline defined in stats.py
    # This function internally calls bin_energy_data, perform_ks_test, perform_chisquared_test, and apply_benjamini_hochberg
    try:
        results = run_statistical_analysis(df)
    except Exception as e:
        raise StatsError(f"Statistical analysis failed: {e}")

    # Structure the output for the JSON artifact
    # The spec requires: test types, statistics, p-values, and rejection flags
    output_data = {
        "metadata": {
            "source_file": str(input_path),
            "total_samples": len(df),
            "columns_processed": list(df.columns),
            "test_types": ["Kolmogorov-Smirnov", "Chi-Squared Goodness-of-Fit"]
        },
        "bin_results": []
    }

    # Flatten the nested results into a list of bin-specific results
    for bin_key, bin_data in results.items():
        bin_entry = {
            "bin_id": bin_key,
            "sample_size": bin_data.get("n_samples", 0),
            "ks_test": {
                "statistic": bin_data["ks"]["statistic"],
                "p_value": bin_data["ks"]["p_value"],
                "rejected_null": bin_data["ks"]["rejected_null"],
                "method": "Two-Sample KS vs Maxwell-Boltzmann"
            },
            "chisquared_test": {
                "statistic": bin_data["chisq"]["statistic"],
                "p_value": bin_data["chisq"]["p_value"],
                "degrees_of_freedom": bin_data["chisq"]["dof"],
                "rejected_null": bin_data["chisq"]["rejected_null"],
                "method": "Chi-Squared Goodness-of-Fit vs Maxwell-Boltzmann"
            },
            "fdr_corrected": {
                "ks_rejection_flag": bin_data["fdr_ks"],
                "chisq_rejection_flag": bin_data["fdr_chisq"]
            }
        }
        output_data["bin_results"].append(bin_entry)

    # Add summary statistics
    total_bins = len(output_data["bin_results"])
    rejected_ks = sum(1 for b in output_data["bin_results"] if b["fdr_corrected"]["ks_rejection_flag"])
    rejected_chisq = sum(1 for b in output_data["bin_results"] if b["fdr_corrected"]["chisq_rejection_flag"])

    output_data["summary"] = {
        "total_bins_analyzed": total_bins,
        "bins_rejecting_ks_null": rejected_ks,
        "bins_rejecting_chisq_null": rejected_chisq,
        "rejection_rate_ks": rejected_ks / total_bins if total_bins > 0 else 0.0,
        "rejection_rate_chisq": rejected_chisq / total_bins if total_bins > 0 else 0.0
    }

    # Write to JSON
    print(f"Writing results to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Successfully generated statistical results: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
