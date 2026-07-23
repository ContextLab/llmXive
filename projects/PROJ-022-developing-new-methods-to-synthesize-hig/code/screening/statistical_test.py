import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Project imports
from utils.logging_config import setup_pipeline_logger
from utils.errors import DataInsufficientError

# Configure logger
logger = setup_pipeline_logger("statistical_test")

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
SCREENING_RESULTS_PATH = DATA_PROCESSED_DIR / "screening_results.json"
PREDICTED_BENCHMARKS_PATH = DATA_PROCESSED_DIR / "predicted_benchmarks.csv"
POWER_ANALYSIS_REPORT_PATH = DATA_REPORTS_DIR / "power_analysis_report.json"
STATISTICAL_TEST_RESULTS_PATH = DATA_REPORTS_DIR / "statistical_test_results.json"

# Sample size assumptions from T014/T033
N_MIN_VALID = 30
POWER_TARGET = 0.8
ALPHA = 0.05

def load_performance_data() -> Tuple[pd.Series, pd.Series]:
    """
    Load predicted performance metrics for bio-candidates and petrochemical benchmarks.
    
    Returns:
        Tuple of (bio_candidate_scores, petro_benchmark_scores)
    
    Raises:
        DataInsufficientError: If data files are missing or insufficient.
    """
    if not SCREENING_RESULTS_PATH.exists():
        raise DataInsufficientError(f"Screening results file not found: {SCREENING_RESULTS_PATH}")
    
    if not PREDICTED_BENCHMARKS_PATH.exists():
        raise DataInsufficientError(f"Predicted benchmarks file not found: {PREDICTED_BENCHMARKS_PATH}")

    # Load screening results to get bio-candidate predictions
    with open(SCREENING_RESULTS_PATH, 'r') as f:
        screening_data = json.load(f)
    
    # Extract bio-candidate predicted performance (assuming 'predicted_permeability' or similar key)
    # Based on T034 output structure
    bio_scores = []
    if 'ranked_candidates' in screening_data:
        for candidate in screening_data['ranked_candidates']:
            # Assuming the score is stored as 'predicted_score' or derived from permeability/selectivity
            # For this implementation, we assume a composite score or permeability is available
            if 'predicted_permeability' in candidate:
                bio_scores.append(candidate['predicted_permeability'])
            elif 'predicted_score' in candidate:
                bio_scores.append(candidate['predicted_score'])
            else:
                # Fallback: try to find any numeric prediction field
                for key, value in candidate.items():
                    if isinstance(value, (int, float)) and key.startswith('predicted'):
                        bio_scores.append(value)
                        break
    
    if len(bio_scores) == 0:
        raise DataInsufficientError("No valid predicted scores found in screening results for bio-candidates.")

    # Load petrochemical benchmarks
    petro_df = pd.read_csv(PREDICTED_BENCHMARKS_PATH)
    # Assuming a column like 'predicted_permeability' or 'predicted_score'
    score_col = None
    for col in petro_df.columns:
        if 'predicted' in col.lower() and 'permeability' in col.lower():
            score_col = col
            break
        elif 'predicted' in col.lower() and 'score' in col.lower():
            score_col = col
            break
    
    if score_col is None:
        # Fallback to first numeric column if specific naming not found
        numeric_cols = petro_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            score_col = numeric_cols[0]
        else:
            raise DataInsufficientError("Could not identify performance score column in predicted benchmarks.")

    petro_scores = petro_df[score_col].dropna().tolist()

    if len(petro_scores) == 0:
        raise DataInsufficientError("No valid predicted scores found in petrochemical benchmarks.")

    logger.info(f"Loaded {len(bio_scores)} bio-candidate scores and {len(petro_scores)} petro-benchmark scores.")
    return pd.Series(bio_scores), pd.Series(petro_scores)

def generate_power_analysis_report(n_bio: int, n_petro: int) -> Dict[str, Any]:
    """
    Generate a Power Analysis Report explicitly stating limitations of the sample size.
    
    This addresses FR-010 and SC-003 requirements regarding statistical rigor.
    
    Args:
        n_bio: Number of bio-candidates
        n_petro: Number of petrochemical benchmarks
    
    Returns:
        Dictionary containing power analysis details and limitations.
    """
    # Calculate total N and effective N for Mann-Whitney U
    total_n = n_bio + n_petro
    # For Mann-Whitney U, power depends on both sample sizes. 
    # We assume balanced design for estimation if not exactly balanced, 
    # but here we use actual counts.
    
    # Since we cannot easily calculate exact power for Mann-Whitney U without specific effect size distribution,
    # we rely on the assumptions from T033 (N=30 total) and document the limitations.
    # The report explicitly states that N=30 is the minimum threshold and may be underpowered for small effects.
    
    report = {
        "report_type": "Power Analysis Limitations",
        "generated_at": str(pd.Timestamp.now()),
        "sample_sizes": {
            "bio_candidates": n_bio,
            "petrochemical_benchmarks": n_petro,
            "total": total_n
        },
        "statistical_test": "Mann-Whitney U Test",
        "assumptions": {
            "alpha": ALPHA,
            "target_power": POWER_TARGET,
            "minimum_sample_size_assumed": N_MIN_VALID
        },
        "limitations": [
          f"Sample size (N={total_n}) is at the minimum threshold (N>=30) required for basic statistical validity.",
          "With N=30, the test has reduced power to detect SMALL effect sizes (Cohen's d < 0.5).",
          "Medium effect sizes (Cohen's d ~ 0.5) may be detectable, but results should be interpreted with caution.",
          "Large effect sizes (Cohen's d > 0.8) are likely to be detected with reasonable power.",
          "The non-parametric nature of the Mann-Whitney U test reduces power compared to a t-test if normality assumptions were met, but is necessary here.",
          "The analysis is based on PREDICTED values from a machine learning model, not experimental ground truth. This introduces model uncertainty not captured in the power analysis.",
          "Conclusions regarding the superiority of bio-candidates are limited by the sample size and the predictive nature of the data."
        ],
        "recommendations": [
          "Experimental validation (FR-009) is required to confirm findings with ground truth data.",
          "Future studies should aim for larger sample sizes (N > 100) to robustly detect medium/small effects.",
          "Effect size reporting (e.g., r = Z/sqrt(N)) is critical alongside p-values."
        ],
        "status": "LIMITED_POWER" if total_n <= 35 else "MODERATE_POWER"
    }
    
    return report

def run_mann_whitney_test(bio_scores: pd.Series, petro_scores: pd.Series) -> Dict[str, Any]:
    """
    Run Mann-Whitney U test and calculate effect size.
    
    Args:
        bio_scores: Series of bio-candidate scores
        petro_scores: Series of petrochemical benchmark scores
    
    Returns:
        Dictionary containing test results.
    """
    # Run Mann-Whitney U test
    # Note: 'alternative' parameter depends on hypothesis. 
    # Here we test if bio-candidates are different (two-sided) or better (greater).
    # Based on T031, we are comparing distributions. Let's assume two-sided for now, 
    # or 'greater' if the hypothesis is that bio-candidates are better.
    # The task description implies a comparison to see if bio-candidates can match/exceed petro.
    # We will use 'two-sided' to be conservative, or 'greater' if the goal is specifically to show superiority.
    # Given the context of "synthesis high-performance", we often look for superiority. 
    # However, without a specific direction in the prompt, 'two-sided' is safer for a general comparison.
    # Let's use 'two-sided' as per standard practice unless specified otherwise.
    u_stat, p_value = stats.mannwhitneyu(bio_scores, petro_scores, alternative='two-sided')
    
    # Calculate effect size (r)
    # r = Z / sqrt(N)
    # We need Z statistic. scipy.stats.mannwhitneyu returns U, but we can calculate Z or use a different approach.
    # scipy.stats.mannwhitneyu does not return Z directly in older versions, but we can approximate or use statsmodels.
    # For simplicity and dependency minimization, we use the approximation:
    # Z = (U - mean_U) / std_U
    n1, n2 = len(bio_scores), len(petro_scores)
    mean_u = (n1 * n2) / 2
    std_u = np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
    
    z_stat = (u_stat - mean_u) / std_u
    effect_size_r = abs(z_stat) / np.sqrt(n1 + n2)
    
    # Interpret effect size
    if effect_size_r < 0.1:
        interpretation = "Negligible"
    elif effect_size_r < 0.3:
        interpretation = "Small"
    elif effect_size_r < 0.5:
        interpretation = "Medium"
    else:
        interpretation = "Large"
    
    return {
        "test": "Mann-Whitney U",
        "statistic": float(u_stat),
        "p_value": float(p_value),
        "z_statistic": float(z_stat),
        "effect_size_r": float(effect_size_r),
        "effect_size_interpretation": interpretation,
        "n_bio": n1,
        "n_petro": n2,
        "total_n": n1 + n2,
        "significant_at_alpha_0.05": p_value < ALPHA
    }

def main():
    """
    Main entry point for the statistical test module.
    
    1. Loads predicted performance data.
    2. Generates the Power Analysis Report with limitations.
    3. Runs the Mann-Whitney U test.
    4. Saves results to JSON.
    """
    logger.info("Starting statistical test analysis (T042).")
    
    try:
        # Load data
        bio_scores, petro_scores = load_performance_data()
        
        # Generate Power Analysis Report (T042 specific requirement)
        logger.info("Generating Power Analysis Report with limitations...")
        power_report = generate_power_analysis_report(len(bio_scores), len(petro_scores))
        
        # Save Power Analysis Report
        with open(POWER_ANALYSIS_REPORT_PATH, 'w') as f:
            json.dump(power_report, f, indent=2)
        logger.info(f"Power Analysis Report saved to {POWER_ANALYSIS_REPORT_PATH}")
        
        # Run statistical test
        logger.info("Running Mann-Whitney U test...")
        test_results = run_mann_whitney_test(bio_scores, petro_scores)
        
        # Combine results
        final_results = {
            "test_results": test_results,
            "power_analysis": power_report,
            "timestamp": str(pd.Timestamp.now()),
            "note": "Results based on PREDICTED values. Experimental validation required for ground truth."
        }
        
        # Save final results
        with open(STATISTICAL_TEST_RESULTS_PATH, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Statistical test results saved to {STATISTICAL_TEST_RESULTS_PATH}")
        logger.info(f"Test Result: p-value = {test_results['p_value']:.4f}, Effect Size (r) = {test_results['effect_size_r']:.4f} ({test_results['effect_size_interpretation']})")
        
        if test_results['significant_at_alpha_0.05']:
            logger.info("Result is statistically significant at alpha=0.05.")
        else:
            logger.info("Result is NOT statistically significant at alpha=0.05.")
        
        return 0
        
    except DataInsufficientError as e:
        logger.error(f"Data insufficient: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during statistical test: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    sys.exit(main())