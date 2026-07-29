"""
Sensitivity Analysis for Prompt Complexity Thresholds.

Implements FR-010: Re-bin data using shifted thresholds (±10 tokens) and report
variance in pass rates to assess robustness of the complexity-performance relationship.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def load_execution_results_for_sensitivity() -> pd.DataFrame:
    """
    Load the execution results CSV containing pass/fail data and token counts.
    """
    input_path = Paths.RESULTS_DIR / "execution_outcomes.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Execution results file not found at {input_path}. "
            "Please run the execution pipeline (Phase 4) first."
        )

    df = pd.read_csv(input_path)
    required_cols = ['complexity_label', 'pass_rate', 'prompt_token_count']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Execution results missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )
    return df


def rebin_by_shifted_thresholds(
    df: pd.DataFrame,
    shift_amount: int = 10,
    base_thresholds: Optional[Dict[str, Tuple[int, int]]] = None
) -> pd.DataFrame:
    """
    Re-assign complexity labels based on shifted token thresholds.

    FR-010 requires testing robustness by shifting thresholds by ±10 tokens.
    We map the continuous 'prompt_token_count' to new complexity bins.

    Args:
        df: DataFrame with 'prompt_token_count' and 'complexity_label'.
        shift_amount: Number of tokens to shift thresholds by (positive or negative).
        base_thresholds: Optional dict mapping label to (min, max) token ranges.
            If None, uses standard project thresholds.

    Returns:
        DataFrame with a new column 'shifted_complexity_label' and updated pass rates.
    """
    # Default thresholds based on project spec (T015 logic)
    if base_thresholds is None:
        # Approximate ranges derived from task descriptions:
        # simple ≤50, moderate 51-150, complex 151-300, very_complex 301-500, degenerate >500
        base_thresholds = {
            'simple': (0, 50),
            'moderate': (51, 150),
            'complex': (151, 300),
            'very_complex': (301, 500),
            'degenerate': (501, float('inf'))
        }

    def get_new_label(token_count: float) -> str:
        """Determine new label based on shifted thresholds."""
        # Apply shift to boundaries
        for label, (low, high) in base_thresholds.items():
            # Shift the boundaries by the amount
            # Note: We shift the *boundaries*, effectively moving the bins
            # If shift is +10, the "simple" bin (0-50) becomes (0-60) effectively?
            # Or does it mean we check if a token count that was "50" (simple)
            # is now "60" (moderate)?
            # Standard sensitivity analysis: Shift the cutoff points.
            # Cutoffs: 50, 150, 300, 500.
            # Shifted Cutoffs: 50+shift, 150+shift, etc.
            pass

        # Let's define cutoffs explicitly for clarity
        cutoffs = [50, 150, 300, 500]
        labels_ordered = ['simple', 'moderate', 'complex', 'very_complex', 'degenerate']

        # Apply shift to cutoffs
        shifted_cutoffs = [c + shift_amount for c in cutoffs]

        # Determine bin
        for i, cutoff in enumerate(shifted_cutoffs):
            if token_count <= cutoff:
                return labels_ordered[i]
        return labels_ordered[-1]

    df = df.copy()
    df['shifted_complexity_label'] = df['prompt_token_count'].apply(get_new_label)

    # Recalculate pass rates per new bin
    # We assume the original 'pass_rate' column is the sample-level metric (0 or 1)
    # or the aggregated rate. If it's aggregated per problem, we need to re-aggregate.
    # Assuming 'pass_rate' here is the outcome (0.0 or 1.0) for the sample.
    if 'pass_rate' in df.columns:
        # If pass_rate is already aggregated (e.g., 0.85), we might just average them.
        # But typically in execution_outcomes.csv, it's the outcome of the run.
        # Let's assume it's the sample outcome (0 or 1) or a float.
        # We calculate the mean pass rate for the new groups.
        agg = df.groupby('shifted_complexity_label')['pass_rate'].mean().reset_index()
        agg.rename(columns={'pass_rate': 'shifted_pass_rate'}, inplace=True)
        df = df.merge(agg, on='shifted_complexity_label', suffixes=('', '_group_avg'))

    return df


def calculate_variance_in_pass_rates(
    df: pd.DataFrame,
    shift_amounts: List[int] = [-10, 10]
) -> Dict[str, Any]:
    """
    Calculate variance in pass rates across different threshold shifts.

    Returns a summary dictionary with the variance metrics.
    """
    results = []
    base_df = df.copy()

    # Calculate base pass rates (using original labels)
    base_rates = base_df.groupby('complexity_label')['pass_rate'].mean()

    for shift in shift_amounts:
        shifted_df = rebin_by_shifted_thresholds(base_df, shift_amount=shift)
        shifted_rates = shifted_df.groupby('shifted_complexity_label')['shifted_pass_rate'].mean()

        # Align indices to compare (only common labels)
        common_labels = base_rates.index.intersection(shifted_rates.index)

        if len(common_labels) > 0:
            # Calculate difference in pass rates for common labels
            diff = (shifted_rates.loc[common_labels] - base_rates.loc[common_labels]).abs()
            mean_diff = diff.mean()
            max_diff = diff.max()
            results.append({
                'shift_amount': shift,
                'mean_pass_rate_change': mean_diff,
                'max_pass_rate_change': max_diff,
                'affected_samples': len(shifted_df)
            })
        else:
            results.append({
                'shift_amount': shift,
                'mean_pass_rate_change': None,
                'max_pass_rate_change': None,
                'affected_samples': len(shifted_df)
            })

    return {
        'base_rates': base_rates.to_dict(),
        'sensitivity_results': results
    }


def write_sensitivity_summary_to_csv(
    summary: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write the sensitivity analysis summary to a CSV file.
    """
    if output_path is None:
        output_path = Paths.RESULTS_DIR / "sensitivity_analysis.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for res in summary['sensitivity_results']:
        rows.append({
            'shift_amount': res['shift_amount'],
            'mean_pass_rate_change': res['mean_pass_rate_change'],
            'max_pass_rate_change': res['max_pass_rate_change'],
            'affected_samples': res['affected_samples']
        })

    df_out = pd.DataFrame(rows)
    df_out.to_csv(output_path, index=False)

    logger.info(f"Sensitivity analysis summary written to {output_path}")
    return output_path


def main():
    """
    Main entry point for running sensitivity analysis.
    """
    logger.info("Starting Sensitivity Analysis (T036)...")

    try:
        # 1. Load data
        df = load_execution_results_for_sensitivity()
        logger.info(f"Loaded {len(df)} execution records.")

        # 2. Run sensitivity analysis
        # We test shifts of -10 and +10 tokens as per FR-010
        summary = calculate_variance_in_pass_rates(df, shift_amounts=[-10, 10])

        # 3. Write results
        write_sensitivity_summary_to_csv(summary)

        logger.info("Sensitivity analysis completed successfully.")
        return summary

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise


if __name__ == "__main__":
    main()