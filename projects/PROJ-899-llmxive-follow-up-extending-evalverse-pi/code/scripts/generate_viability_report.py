"""
Script to generate the final dimension viability report (T018).
Reads correlation data and sensitivity analysis results to produce
data/dimension_viability.csv.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from src.reports.generate import main as reports_main
from src.utils import setup_logging, get_logger, ensure_directories, write_csv

def load_correlation_results():
    """Load correlation results from T016."""
    path = Path("data/processed/correlations.csv")
    if not path.exists():
        raise FileNotFoundError(f"Correlation results not found at {path}")
    df = pd.read_csv(path)
    required_cols = ['dimension', 'pearson_r', 'spearman_r', 'lower_ci', 'upper_ci']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {path}")
    return df

def load_adjusted_p_values():
    """Load adjusted p-values from T020."""
    path = Path("data/permutation_results.csv")
    if not path.exists():
        # If permutation test wasn't run, we might not have adjusted p-values.
        # In that case, we can use raw p-values if available, or default to 1.0.
        # However, the task T020 is a prerequisite for T018 in the spec logic
        # (implied by "Generate final... with adjusted_p").
        # We'll check if the file exists. If not, we'll try to generate a placeholder
        # or raise an error if the data is strictly required.
        # Given the execution failure context, we must ensure the file exists.
        # If T020 failed previously, we need to ensure T020 runs or handle the missing file.
        # For this specific task T018, we assume T020 has produced the file.
        # If it doesn't exist, we cannot fabricate. We raise an error.
        raise FileNotFoundError(f"Permutation results not found at {path}. T020 must be completed.")
    df = pd.read_csv(path)
    required_cols = ['dimension', 'adjusted_p']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {path}")
    return df[['dimension', 'adjusted_p']]

def load_status_from_reports():
    """Load dimension status from T017 reports generation."""
    # T017 generates the logic for 'status'.
    # The reports/generate.py module's main function should produce the status logic.
    # We will re-implement the logic here to ensure consistency or call the function.
    # Based on the API surface, src.reports.generate has classify_dimension_status.
    # Let's assume the correlation data is enough to re-classify.
    # Actually, T017's output is likely intermediate or the status is derived directly.
    # We will derive status here using the logic from T017 description:
    # "feature-sufficient" (r >= 0.85) or "VLM-required" (lower 95% CI < 0.70).
    # We'll read the correlation data and apply the logic.
    # If T017 produced a file with status, we should use that.
    # The task T017 description says "Implement logic... in src/reports/generate.py".
    # It doesn't explicitly say it writes a file with status, but T018 needs it.
    # We will derive it here from the correlation data to be safe and consistent.
    return None

def classify_dimension_status(row):
    """
    Classify dimension as 'feature-sufficient' or 'VLM-required'.
    Logic from T017:
    - 'feature-sufficient' if r >= 0.85
    - 'VLM-required' if lower 95% CI < 0.70
    - Note: The task says "or VLM-required (specifically checking lower 95% CI < 0.70)".
    - It implies a priority or specific condition.
    - If r >= 0.85, it's sufficient.
    - If not, check if lower_ci < 0.70 -> VLM-required.
    - What if 0.70 <= lower_ci < 0.85? The spec doesn't explicitly say, but usually it's "inconclusive" or "VLM-required".
    - Given the binary nature of the report, we'll assume:
      - If r >= 0.85: feature-sufficient
      - Else if lower_ci < 0.70: VLM-required
      - Else: VLM-required (conservative) or a third category?
    - Re-reading T017: "flag dimensions as 'feature-sufficient' (r ≥ 0.85) or 'VLM-required' (specifically checking lower 95% CI < 0.70)".
    - This suggests two categories. If it doesn't meet the first, it falls to the second check.
    - Let's assume if r < 0.85, we check the CI. If lower_ci < 0.70, it's VLM-required.
    - If lower_ci >= 0.70 but r < 0.85, it's ambiguous. We'll default to 'VLM-required' for safety
      or 'inconclusive'. However, the output schema for T018 is `[dimension, pearson_r, lower_ci, upper_ci, status, adjusted_p]`.
      It expects a status. Let's assume 'VLM-required' for anything not 'feature-sufficient'.
    """
    r = row['pearson_r']
    lower_ci = row['lower_ci']

    if r >= 0.85:
        return 'feature-sufficient'
    elif lower_ci < 0.70:
        return 'VLM-required'
    else:
        # Ambiguous case: r < 0.85 but lower_ci >= 0.70.
        # Given the binary choice in the description, we default to VLM-required.
        return 'VLM-required'

def main():
    """Main function to generate the dimension viability report."""
    logger = get_logger(__name__)
    logger.info("Starting dimension viability report generation (T018).")

    # Ensure output directory exists
    ensure_directories(["data"])

    # Load inputs
    try:
        corr_df = load_correlation_results()
        adj_p_df = load_adjusted_p_values()
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Input file validation error: {e}")
        sys.exit(1)

    # Merge data
    if not pd.api.types.is_string_dtype(corr_df['dimension']):
        corr_df['dimension'] = corr_df['dimension'].astype(str)
    if not pd.api.types.is_string_dtype(adj_p_df['dimension']):
        adj_p_df['dimension'] = adj_p_df['dimension'].astype(str)

    merged_df = pd.merge(corr_df, adj_p_df, on='dimension', how='left')

    # Fill missing adjusted_p with 1.0 if any (though T020 should cover all)
    merged_df['adjusted_p'] = merged_df['adjusted_p'].fillna(1.0)

    # Classify status
    merged_df['status'] = merged_df.apply(classify_dimension_status, axis=1)

    # Select and order columns for output
    output_cols = ['dimension', 'pearson_r', 'lower_ci', 'upper_ci', 'status', 'adjusted_p']
    # Ensure all columns exist
    for col in output_cols:
        if col not in merged_df.columns:
            logger.error(f"Missing column {col} in merged data")
            sys.exit(1)

    output_df = merged_df[output_cols]

    # Write output
    output_path = Path("data/dimension_viability.csv")
    write_csv(output_df, str(output_path))
    logger.info(f"Successfully wrote dimension viability report to {output_path}")

    return 0

if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
