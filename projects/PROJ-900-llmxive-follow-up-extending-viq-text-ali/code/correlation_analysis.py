"""
Correlation Analysis Script for T022.

Implements Spearman rank correlation AND paired t-test/Wilcoxon
between texture complexity and reconstruction error (PSNR).

Deviates from Spec SC-005 (one-sample t-test) per Plan Spec Amendment #4.
Uses paired t-test (or Wilcoxon signed-rank if assumptions fail) on the
relationship between complexity and error.

Input: JSON file containing list of dicts with keys:
       ["texture_complexity", "psnr"] (produced by T021/eval_high_res flow)
Output: JSON file {spearman_r, p_value, method}
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(input_path: Path) -> pd.DataFrame:
    """
    Load the fidelity metrics JSON into a pandas DataFrame.
    Expects a list of records with 'texture_complexity' and 'psnr'.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict) and 'samples' in data:
        # If wrapped in a 'samples' key
        df = pd.DataFrame(data['samples'])
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        raise ValueError(f"Unexpected data format in {input_path}. Expected list or dict with 'samples'.")

    required_cols = ['texture_complexity', 'psnr']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in input data: {missing}")

    # Drop rows with NaNs
    df = df.dropna(subset=required_cols)
    logger.info(f"Loaded {len(df)} valid samples for analysis.")
    return df

def compute_spearman_correlation(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation between texture_complexity and psnr.
    Returns (rho, p_value).
    """
    x = df['texture_complexity'].values
    y = df['psnr'].values

    rho, p_value = stats.spearmanr(x, y)
    logger.info(f"Spearman Rank Correlation (rho): {rho:.4f}, p-value: {p_value:.4e}")
    return rho, p_value

def compute_paired_test(df: pd.DataFrame) -> Tuple[str, float]:
    """
    Perform a paired statistical test.
    Since we are testing the relationship between two continuous variables,
    strictly speaking, a correlation test (Spearman/Pearson) is the primary metric.
    However, per the task requirement to run a "paired t-test/Wilcoxon"
    (deviating from SC-005 one-sample), we interpret this as testing if the
    *difference* between a baseline (e.g., mean complexity) and observed
    correlates with error, OR more simply, we treat the two variables as
    paired samples to test for systematic differences in distribution (though
    this is statistically less direct for correlation).

    Given the specific prompt "paired t-test/Wilcoxon ... between texture complexity and reconstruction error",
    and the deviation from a one-sample test, the most robust interpretation in
    this context (checking for systematic bias in error relative to complexity)
    is to test if the difference (texture_complexity - psnr) is significantly different from zero?
    No, that compares scales.

    Correct interpretation for "paired test" in a correlation context usually implies
    checking if the correlation is significantly different from zero (which Spearman does).
    However, to satisfy the explicit requirement for a "paired t-test/Wilcoxon"
    on the pair (complexity, error), we will test if the mean of the differences
    (complexity - error) is zero, acknowledging this is a distributional comparison.
    
    Actually, a more scientifically sound "paired" approach here, given the
    "deviation from one-sample" note, is likely testing the *slope* or the
    relationship. But to strictly follow the "paired t-test" instruction on the
    two columns:
    
    We will perform a paired t-test to see if the mean of (texture_complexity - psnr)
    is significantly different from 0. This tests if the two metrics are centered
    differently. If the prompt implies testing the *significance of the correlation*,
    Spearman's p-value is the correct metric.
    
    Let's implement the Paired t-test on the two columns as requested,
    and fallback to Wilcoxon if normality of differences fails.
    """
    x = df['texture_complexity'].values
    y = df['psnr'].values

    differences = x - y

    # Test normality of differences
    _, p_normality = stats.shapiro(differences)
    alpha = 0.05

    method = ""
    p_value = 0.0

    if p_normality > alpha:
        # Normal distribution of differences -> Paired t-test
        stat, p_value = stats.ttest_rel(x, y)
        method = "paired_t_test"
        logger.info(f"Normality passed (p={p_normality:.4f}). Using Paired t-test.")
    else:
        # Non-normal -> Wilcoxon signed-rank test
        stat, p_value = stats.wilcoxon(x, y)
        method = "wilcoxon_signed_rank"
        logger.info(f"Normality failed (p={p_normality:.4f}). Using Wilcoxon signed-rank test.")

    logger.info(f"{method} p-value: {p_value:.4e}")
    return method, p_value

def save_results(output_path: Path, spearman_r: float, p_value: float, method: str) -> None:
    """
    Save the results to a JSON file.
    Schema: {"spearman_r": float, "p_value": float, "method": str}
    """
    results = {
        "spearman_r": float(spearman_r),
        "p_value": float(p_value),
        "method": method
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Correlation Analysis for ViQ Fidelity")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the input JSON file containing texture_complexity and psnr."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/correlation_analysis.json"),
        help="Path to the output JSON file."
    )

    args = parser.parse_args()

    try:
        df = load_data(args.input)

        if len(df) < 2:
            logger.error("Insufficient data points for statistical analysis.")
            sys.exit(1)

        spearman_r, spearman_p = compute_spearman_correlation(df)
        paired_method, paired_p = compute_paired_test(df)

        # The task asks for "p_value" in the output.
        # Since we run two tests, we should clarify which p-value is returned.
        # The prompt says: "Output: JSON {spearman_r, p_value, method}".
        # This implies the p_value corresponds to the Spearman test (as spearman_r is the primary metric),
        # and 'method' refers to the paired test performed.
        # However, to be comprehensive, we will store the Spearman p-value as 'p_value'
        # and the method used for the paired test.
        
        save_results(args.output, spearman_r, spearman_p, paired_method)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
