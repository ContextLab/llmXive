"""
T027 Implementation: One-sample test on Power Gap.

Performs a one-sample t-test (or Wilcoxon signed-rank test if assumptions fail)
on the 'power_gap' column from data/derived/power_analysis.csv against a null
hypothesis of zero.

Output: data/derived/regression_diagnostics.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PATH = Path("data/derived/power_analysis.csv")
OUTPUT_PATH = Path("data/derived/regression_diagnostics.json")
POWER_GAP_COLUMN = "power_gap"
NULL_HYPOTHESIS = 0.0
ALPHA = 0.05

def load_power_analysis_data(input_path: Path) -> pd.DataFrame:
    """Load the power analysis dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    if POWER_GAP_COLUMN not in df.columns:
        raise ValueError(f"Column '{POWER_GAP_COLUMN}' not found in {input_path}. "
                       f"Available columns: {list(df.columns)}")
    
    return df

def filter_valid_power_gaps(df: pd.DataFrame) -> pd.Series:
    """Filter out NaN and invalid power gap values."""
    valid_series = df[POWER_GAP_COLUMN].dropna()
    valid_series = valid_series[np.isfinite(valid_series)]
    
    if len(valid_series) == 0:
        raise ValueError("No valid power gap values found after filtering.")
    
    logger.info(f"Filtered {len(df) - len(valid_series)} invalid records. "
               f"Remaining valid records: {len(valid_series)}")
    return valid_series

def perform_statistical_test(
    sample: pd.Series, 
    null_hypothesis: float = NULL_HYPOTHESIS,
    alpha: float = ALPHA
) -> Dict[str, Any]:
    """
    Perform one-sample t-test. Falls back to Wilcoxon if normality assumption fails.
    
    Returns a dictionary with test results.
    """
    n = len(sample)
    mean_val = float(sample.mean())
    std_val = float(sample.std(ddof=1))
    
    result: Dict[str, Any] = {
        "n": n,
        "mean_power_gap": mean_val,
        "std_power_gap": std_val,
        "null_hypothesis": null_hypothesis,
        "alpha": alpha
    }
    
    # Check normality assumption (Shapiro-Wilk test)
    # Note: Shapiro-Wilk is sensitive to large N. For very large N, we might skip or use KS.
    # Given typical study counts, we'll use Shapiro-Wilk if N < 5000, else KS.
    normality_p_value = None
    is_normal = False
    
    if n > 1:
        try:
            if n <= 5000:
                stat, p_val = stats.shapiro(sample)
                normality_p_value = float(p_val)
                is_normal = (p_val > alpha)
            else:
                # Kolmogorov-Smirnov test for large N
                stat, p_val = stats.kstest(sample, 'norm', args=(mean_val, std_val))
                normality_p_value = float(p_val)
                is_normal = (p_val > alpha)
        except Exception as e:
            logger.warning(f"Normality test failed: {e}. Proceeding with t-test assumption.")
            is_normal = True # Default to t-test if test fails
    
    result["normality_test"] = "Shapiro-Wilk" if n <= 5000 else "Kolmogorov-Smirnov"
    result["normality_p_value"] = normality_p_value
    result["is_normal"] = is_normal
    
    if is_normal and n > 1:
        # One-sample t-test
        t_stat, p_val = stats.ttest_1samp(sample, null_hypothesis)
        test_type = "one_sample_t_test"
        result["test_statistic"] = float(t_stat)
        result["p_value"] = float(p_val)
        logger.info(f"Performing one-sample t-test: t={t_stat:.4f}, p={p_val:.4f}")
    else:
        # Wilcoxon signed-rank test
        if n > 1:
            w_stat, p_val = stats.wilcoxon(sample, mu=null_hypothesis)
            test_type = "wilcoxon_signed_rank_test"
            result["test_statistic"] = float(w_stat)
            result["p_value"] = float(p_val)
            logger.info(f"Normality assumption failed. Performing Wilcoxon test: W={w_stat:.4f}, p={p_val:.4f}")
        else:
            # Cannot perform test with n=1
            result["test_type"] = "insufficient_data"
            result["test_statistic"] = None
            result["p_value"] = None
            logger.warning("Insufficient data (n=1) for statistical testing.")
            return result
    
    result["test_type"] = test_type
    
    # Determine conclusion
    is_significant = (result["p_value"] is not None) and (result["p_value"] < alpha)
    result["is_significant"] = is_significant
    
    if is_significant:
        direction = "greater" if mean_val > 0 else "less"
        result["conclusion"] = (
            f"Reject null hypothesis. The mean power gap is significantly "
            f"{direction} than {null_hypothesis} (p < {alpha}). "
            f"This suggests a systematic bias in planned power."
        )
    else:
        result["conclusion"] = (
            f"Fail to reject null hypothesis. There is insufficient evidence to conclude "
            f"that the mean power gap differs from {null_hypothesis} (p >= {alpha})."
        )
    
    return result

def write_results(results: Dict[str, Any], output_path: Path) -> None:
    """Write results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results written to {output_path}")

def main() -> int:
    """Main entry point."""
    try:
        # Load data
        df = load_power_analysis_data(INPUT_PATH)
        
        # Filter valid values
        valid_gaps = filter_valid_power_gaps(df)
        
        # Perform test
        results = perform_statistical_test(valid_gaps)
        
        # Write output
        write_results(results, OUTPUT_PATH)
        
        print(f"Analysis complete. Output: {OUTPUT_PATH}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
