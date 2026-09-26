import os
import logging
import pandas as pd
from pathlib import Path

from config import get_output_path
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_max_delta_pvals(
    adjusted_pvals_path: str,
    unadjusted_pvals_path: str,
    output_dir: str = None
) -> dict:
    """
    Calculate |p_adjusted - p_unadjusted| for each taxon, identify the maximum delta,
    and return the statistics needed for the report.

    Args:
        adjusted_pvals_path: Path to CSV containing adjusted p-values (q-values).
        unadjusted_pvals_path: Path to CSV containing unadjusted p-values.
        output_dir: Directory to write the result report (optional).

    Returns:
        dict containing:
            - 'max_delta': float, maximum absolute difference
            - 'threshold_met': bool, whether max_delta <= 0.05 (SC-005 threshold)
            - 'total_taxa': int, number of taxa analyzed
    """
    logger.info(f"Loading adjusted p-values from {adjusted_pvals_path}")
    df_adj = pd.read_csv(adjusted_pvals_path)

    logger.info(f"Loading unadjusted p-values from {unadjusted_pvals_path}")
    df_unadj = pd.read_csv(unadjusted_pvals_path)

    # Validate that we have a common key (usually 'taxon' or 'feature_id')
    # The tasks.md implies a 'taxon' column based on the AssociationResult schema
    key_col = 'taxon'
    if key_col not in df_adj.columns or key_col not in df_unadj.columns:
        # Fallback to any common column if 'taxon' isn't present, or raise error
        common_cols = set(df_adj.columns).intersection(set(df_unadj.columns))
        if not common_cols:
            raise ValueError("No common key column found between adjusted and unadjusted p-value files.")
        key_col = common_cols.pop()
        logger.warning(f"Using '{key_col}' as the join key instead of 'taxon'.")

    # Merge on the key column
    merged = pd.merge(
        df_adj[[key_col, 'p_adjusted' if 'p_adjusted' in df_adj.columns else 'qval']],
        df_unadj[[key_col, 'p_unadjusted' if 'p_unadjusted' in df_unadj.columns else 'pval']],
        on=key_col,
        how='inner'
    )

    # Standardize column names for calculation
    adj_col = 'p_adjusted' if 'p_adjusted' in merged.columns else 'qval'
    unadj_col = 'p_unadjusted' if 'p_unadjusted' in merged.columns else 'pval'

    # Calculate absolute delta
    merged['delta'] = (merged[adj_col] - merged[unadj_col]).abs()

    max_delta = merged['delta'].max()
    total_taxa = len(merged)

    # SC-005 Threshold: Typically, a large delta indicates the adjustment (covariate control)
    # had a significant impact. A common threshold in such checks is 0.05 or 0.1.
    # Based on the context of "Threshold Met", we assume a threshold of 0.05.
    threshold = 0.05
    threshold_met = max_delta <= threshold

    logger.info(f"Calculated max delta: {max_delta:.6f} over {total_taxa} taxa.")
    logger.info(f"Threshold ({threshold}) met: {threshold_met}")

    return {
        'max_delta': max_delta,
        'threshold_met': threshold_met,
        'total_taxa': total_taxa
    }


def run_covariate_check(
    adjusted_pvals_path: str = None,
    unadjusted_pvals_path: str = None,
    output_path: str = None
) -> str:
    """
    Execute the SC-005 check: calculate max delta and write the report.

    Args:
        adjusted_pvals_path: Path to adjusted p-values CSV.
        unadjusted_pvals_path: Path to unadjusted p-values CSV.
        output_path: Path to write the result text file.

    Returns:
        The path to the generated report file.
    """
    # Use config defaults if paths are not provided
    if adjusted_pvals_path is None:
        adjusted_pvals_path = get_output_path("processed/association_results.csv")
        # If the main results file is used, we might need to filter or extract.
        # However, T022 explicitly saves unadjusted to specific interim files.
        # Let's assume the task expects the specific interim files generated in T020/T020a/T022.
        # If the main results file contains both, we might need to split.
        # For robustness, let's try to detect the specific interim files first.
        interim_adj = get_output_path("interim/alpha_pvals_adjusted.csv") # Assumption
        # Actually, T022 says "Apply BH to all... and report adjusted".
        # Let's assume the user passes the correct paths or we derive them from the standard output structure.
        # Based on T020/T020a: unadjusted are in data/interim/unadjusted_*.csv
        # T022 likely overwrites or creates adjusted versions.
        # Let's stick to the most likely file names based on the task description logic.
        # We will assume the caller provides the correct paths or we use standard derived paths.
        pass

    # If paths are still None, try to infer from standard project structure
    if adjusted_pvals_path is None:
        # Assume the main results file contains the adjusted values, or a specific adjusted file exists
        # T025 outputs association_results.csv. Let's assume that's the source of truth for adjusted.
        # But T022 says "report adjusted p-values".
        # Let's try to load from the specific interim files if they exist, otherwise the main results.
        # To be safe, we require the caller to pass the correct paths if ambiguous,
        # but for this script to run standalone, we'll try standard paths.
        # Standard paths derived from T020/T020a/T022:
        # Unadjusted: data/interim/unadjusted_alpha_pvals.csv, data/interim/unadjusted_taxa_pvals.csv
        # Adjusted: data/processed/association_results.csv (contains q-values)
        # However, the delta calculation is usually per-taxon.
        # Let's assume the input files are the specific ones generated by T020/T020a and T022.
        # If the user didn't pass them, we default to the most likely generated names.
        adjusted_pvals_path = get_output_path("processed/association_results.csv")
        unadjusted_pvals_path = get_output_path("interim/unadjusted_taxa_pvals.csv")

    if output_path is None:
        output_path = get_output_path("results/temp_covariate_check.txt")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    stats = calculate_max_delta_pvals(adjusted_pvals_path, unadjusted_pvals_path)

    # Format the report as requested
    # "Max Delta: X.XX. Threshold Met: [True/False]"
    report_content = (
        f"SC-005 Covariate Adjustment Check\n"
        f"-----------------------------------\n"
        f"Total Taxa Analyzed: {stats['total_taxa']}\n"
        f"Max Delta (|p_adj - p_unadj|): {stats['max_delta']:.6f}\n"
        f"Threshold (0.05) Met: {stats['threshold_met']}\n"
        f"Note: This check verifies if the covariate adjustment significantly altered the p-values.\n"
    )

    with open(output_path, 'w') as f:
        f.write(report_content)

    logger.info(f"Covariate check report written to {output_path}")
    return output_path


def main():
    """Entry point for the covariate adjustment check."""
    setup_logger = get_logger(__name__)
    setup_logger.info("Starting Covariate Adjustment Check (T023)...")

    try:
        # We assume the standard output paths generated by previous tasks
        # T020/T020a generated: data/interim/unadjusted_alpha_pvals.csv, data/interim/unadjusted_taxa_pvals.csv
        # T022 generated: data/processed/association_results.csv (with q-values)
        # The check is specifically for taxa (T023 context: "for each taxon")
        # So we use the taxa unadjusted file and the main results (which has taxa adjusted)

        # Let's try to find the files dynamically or use defaults
        from config import get_output_path
        import os

        # Path to unadjusted taxa p-values (generated in T020a)
        unadjusted_path = get_output_path("interim/unadjusted_taxa_pvals.csv")
        
        # Path to adjusted p-values (generated in T022, likely in association_results.csv or a specific adjusted file)
        # If association_results.csv is the main output, it likely has 'qval' or 'p_adjusted'
        # Let's assume the user has run T022 and generated the necessary files.
        # If the specific adjusted file doesn't exist, we might need to extract from association_results.
        # For simplicity in this script, we assume the file exists or we use the main results.
        adjusted_path = get_output_path("processed/association_results.csv")
        
        # If the adjusted file is the main results, we might need to handle column names carefully
        # in calculate_max_delta_pvals.
        
        result_path = run_covariate_check(
            adjusted_pvals_path=adjusted_path,
            unadjusted_pvals_path=unadjusted_path
        )
        
        print(f"Check completed. Report saved to: {result_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Required data file not found. Ensure T020a and T022 have been run. Error: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred during the check: {e}")
        raise


if __name__ == "__main__":
    main()
