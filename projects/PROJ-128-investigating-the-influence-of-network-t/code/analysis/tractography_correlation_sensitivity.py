"""
Tractography-Function Correlation Sensitivity Analysis (Task T043)

Re-runs the correlation analysis (US2) for each tractography confidence threshold
to assess how the association between structural and functional metrics changes
as the structural data becomes "cleaner" (higher confidence).

Output: data/processed/tractography_correlation_sensitivity.csv
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.correlation import run_correlation_analysis, benjamini_hochberg_fdr
from config import get_config_dict

def load_structural_metrics_by_threshold(threshold: float) -> pd.DataFrame:
    """
    Load structural metrics that were pre-computed for a specific confidence threshold.
    The file naming convention is: data/processed/structural_metrics_threshold_<val>.csv
    """
    config = get_config_dict()
    base_path = Path(config["processed_dir"])
    filename = f"structural_metrics_threshold_{threshold:.1f}.csv"
    filepath = base_path / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Structural metrics for confidence threshold {threshold} not found. "
            f"Expected path: {filepath}. "
            "Ensure T042 (tractography_sensitivity.py) has been executed to generate these files."
        )

    df = pd.read_csv(filepath)
    return df

def load_dynamic_metrics() -> pd.DataFrame:
    """
    Load the dynamic functional metrics (dwell time, visited states).
    These are independent of the structural threshold.
    """
    config = get_config_dict()
    base_path = Path(config["processed_dir"])
    filepath = base_path / "dynamic_metrics.csv"

    if not filepath.exists():
        raise FileNotFoundError(
            f"Dynamic metrics file not found at {filepath}. "
            "Ensure T017 (functional pipeline) has been executed."
        )

    df = pd.read_csv(filepath)
    return df

def run_correlation_for_threshold(
    structural_df: pd.DataFrame,
    dynamic_df: pd.DataFrame,
    threshold: float
) -> pd.DataFrame:
    """
    Run the full correlation pipeline (normality check, correlation, FDR)
    for a specific structural threshold and merge results with the threshold label.
    """
    # Merge structural and dynamic metrics on subject_id
    # Assuming both have 'subject_id' column
    merged = pd.merge(structural_df, dynamic_df, on="subject_id", how="inner")

    if merged.empty:
        raise ValueError("No overlapping subjects found between structural and dynamic metrics.")

    # Run correlation analysis
    # The run_correlation_analysis function expects two dataframes or a merged one with specific columns.
    # Based on T024/T025 implementation, it typically takes the merged data and column lists.
    # We assume the standard columns: global_efficiency, clustering, modularity (struct)
    # and mean_dwell_time, num_visited_states (dynamic).
    # We will pass the merged DF and let the function detect columns or we specify them.
    # Looking at T024/T025, the function likely takes the full merged DF.

    # Define structural and dynamic columns explicitly to avoid ambiguity
    struct_cols = ["global_efficiency", "clustering", "modularity"]
    dynamic_cols = ["mean_dwell_time", "num_visited_states", "num_visits"]

    # Filter to only these columns for the analysis
    analysis_data = merged[["subject_id"] + struct_cols + dynamic_cols]

    results = run_correlation_analysis(analysis_data, struct_cols, dynamic_cols)

    # Add the threshold column to every row
    results["threshold"] = threshold

    return results

def main():
    """
    Main entry point for T043.
    Iterates through confidence thresholds, loads corresponding structural metrics,
    runs correlation with dynamic metrics, and aggregates results.
    """
    config = get_config_dict()
    thresholds = config.get("TRACTOGRAPHY_CONFIDENCE_THRESHOLDS", [0.0, 0.2, 0.4, 0.6, 0.8])

    print(f"Starting Tractography-Function Correlation Sensitivity Analysis (T043)...")
    print(f"Configured thresholds: {thresholds}")

    all_results = []

    try:
        # Load dynamic metrics once (they are constant across thresholds)
        print("Loading dynamic metrics...")
        dynamic_df = load_dynamic_metrics()

        for thresh in thresholds:
            print(f"Processing threshold: {thresh}")
            try:
                # Load structural metrics for this specific threshold
                structural_df = load_structural_metrics_by_threshold(thresh)

                # Run correlation
                results = run_correlation_for_threshold(structural_df, dynamic_df, thresh)
                all_results.append(results)

                print(f"  -> Completed threshold {thresh}: {len(results)} correlations found.")

            except FileNotFoundError as e:
                print(f"  -> ERROR: {e}")
                print(f"  -> Skipping threshold {thresh}. Ensure T042 has generated the required files.")
                continue
            except Exception as e:
                print(f"  -> CRITICAL ERROR for threshold {thresh}: {e}")
                raise

        if not all_results:
            raise RuntimeError("No results were generated for any threshold.")

        # Combine all results
        final_df = pd.concat(all_results, ignore_index=True)

        # Save output
        config = get_config_dict()
        output_path = Path(config["processed_dir"]) / "tractography_correlation_sensitivity.csv"
        final_df.to_csv(output_path, index=False)

        print(f"Successfully saved results to: {output_path}")
        print(f"Total rows: {len(final_df)}")
        print(f"Columns: {list(final_df.columns)}")

        # Summary statistics
        print("\n--- Summary ---")
        print(f"Number of thresholds processed: {final_df['threshold'].nunique()}")
        print(f"Number of metric pairs: {final_df['pair'].nunique() if 'pair' in final_df.columns else 'N/A'}")

        # Count significant findings per threshold
        if 'fdr_corrected' in final_df.columns:
            sig_counts = final_df.groupby('threshold')['fdr_corrected'].sum()
            print("\nSignificant findings per threshold:")
            print(sig_counts)

    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()