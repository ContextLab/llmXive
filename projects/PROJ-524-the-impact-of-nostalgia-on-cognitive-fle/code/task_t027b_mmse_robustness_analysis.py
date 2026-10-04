"""
T027b: MMSE Robustness Analysis
Re-runs the statistical analysis (Welch's t-test, Bonferroni, Effect Size, Power)
on the dataset excluding MMSE criteria (data/processed/cleaned_dataset_no_mmse.csv).
Writes results to data/results/robustness_report.json.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from statsmodels.stats.power import t_ind_solve_power
from statsmodels.stats.weightstats import ttest_ind

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project root relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_RESULTS_DIR = BASE_DIR / "data" / "results"

# Ensure results directory exists
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_no_mmse_dataset() -> pd.DataFrame:
    """
    Loads the dataset that was generated WITHOUT MMSE filtering.
    Path: data/processed/cleaned_dataset_no_mmse.csv
    """
    file_path = DATA_PROCESSED_DIR / "cleaned_dataset_no_mmse.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file for robustness analysis not found: {file_path}. "
            "Ensure T012e (MMSE Exclusion) has been run to generate the 'no_mmse' dataset."
        )
    
    logger.info(f"Loading no-MMSE dataset from {file_path}")
    df = pd.read_csv(file_path)
    
    # Basic validation
    required_cols = ['participant_id', 'stimulus_type', 'perseverative_errors', 'categories_completed', 'age']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")
    
    # Filter out rows with NaN in key metrics
    initial_count = len(df)
    df = df.dropna(subset=['perseverative_errors', 'categories_completed'])
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing scores from no-MMSE dataset.")
    
    if len(df) < 2:
        raise ValueError("Dataset too small for analysis (need at least 2 records).")
        
    return df

def welch_t_test(group1: pd.Series, group2: pd.Series) -> dict:
    """
    Performs Welch's t-test (independent samples, unequal variance).
    Returns t-statistic, p-value, and degrees of freedom.
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Sample size too small for t-test (need >= 2 per group).")
    
    # scipy.stats.ttest_ind with equal_var=False performs Welch's t-test
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    df = len(group1) + len(group2) - 2 # Approximation for reporting, though Welch uses specific df
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "degrees_of_freedom_approx": float(df),
        "n_group1": int(len(group1)),
        "n_group2": int(len(group2))
    }

def bonferroni_correction(p_values: list) -> list:
    """
    Applies Bonferroni correction to a list of p-values.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    alpha = 0.05
    corrected_p = [min(p * n_tests, 1.0) for p in p_values]
    return corrected_p

def calculate_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculates Cohen's d effect size.
    d = (mean1 - mean2) / pooled_std
    """
    mean1, mean2 = group1.mean(), group2.mean()
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return float((mean1 - mean2) / pooled_std)

def calculate_power_and_mdes(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> dict:
    """
    Calculates statistical power and Minimum Detectable Effect Size (MDES).
    """
    n_obs = (n1 + n2) / 2
    # Using t_ind_solve_power from statsmodels
    # power = 0.8 is standard target
    try:
        # Calculate power for observed effect size
        power = t_ind_solve_power(effect_size=abs(effect_size), nobs1=n_obs, alpha=alpha, ratio=n2/n1, alternative='two-sided')
        
        # Calculate MDES for 80% power
        mdes = t_ind_solve_power(effect_size=None, power=0.8, nobs1=n_obs, alpha=alpha, ratio=n2/n1, alternative='two-sided')
        
        return {
            "observed_power": float(power),
            "minimum_detectable_effect_size": float(mdes),
            "target_power": 0.8
        }
    except Exception as e:
        logger.warning(f"Power analysis failed: {e}")
        return {
            "observed_power": None,
            "minimum_detectable_effect_size": None,
            "error": str(e)
        }

def run_robustness_analysis(df: pd.DataFrame) -> dict:
    """
    Runs the full analysis pipeline on the provided dataset.
    """
    # Split by stimulus type
    # Ensure 'nostalgia' and 'control' exist
    if 'nostalgia' not in df['stimulus_type'].values or 'control' not in df['stimulus_type'].values:
        raise ValueError("Dataset must contain both 'nostalgia' and 'control' groups.")
    
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']
    control_group = df[df['stimulus_type'] == 'control']
    
    logger.info(f"Group sizes - Nostalgia: {len(nostalgia_group)}, Control: {len(control_group)}")
    
    results = {
        "dataset_source": "cleaned_dataset_no_mmse.csv",
        "description": "Robustness analysis excluding MMSE criteria",
        "groups": {
            "nostalgia": {"n": len(nostalgia_group), "mean_errors": float(nostalgia_group['perseverative_errors'].mean()), "mean_cats": float(nostalgia_group['categories_completed'].mean())},
            "control": {"n": len(control_group), "mean_errors": float(control_group['perseverative_errors'].mean()), "mean_cats": float(control_group['categories_completed'].mean())}
        },
        "metrics": {}
    }
    
    metrics_to_test = ['perseverative_errors', 'categories_completed']
    all_p_values = []
    
    for metric in metrics_to_test:
        g1 = nostalgia_group[metric]
        g2 = control_group[metric]
        
        # 1. Welch's t-test
        t_test_res = welch_t_test(g1, g2)
        
        # 2. Effect Size
        cohens_d = calculate_cohen_d(g1, g2)
        
        # 3. Power & MDES
        power_res = calculate_power_and_mdes(cohens_d, t_test_res['n_group1'], t_test_res['n_group2'])
        
        all_p_values.append(t_test_res['p_value'])
        
        results["metrics"][metric] = {
            "welch_t_test": t_test_res,
            "cohens_d": cohens_d,
            "power_analysis": power_res
        }
    
    # 4. Bonferroni Correction
    corrected_p = bonferroni_correction(all_p_values)
    for i, metric in enumerate(metrics_to_test):
        results["metrics"][metric]["bonferroni_corrected_p"] = corrected_p[i]
        # Determine significance
        results["metrics"][metric]["is_significant_bonferroni"] = corrected_p[i] < 0.05
    
    return results

def save_report(results: dict, output_path: Path):
    """
    Saves the robustness report to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Robustness report saved to {output_path}")

def main():
    """
    Main entry point for T027b.
    """
    try:
        # 1. Load data
        df = load_no_mmse_dataset()
        
        # 2. Run analysis
        logger.info("Starting robustness analysis (T027b)...")
        report = run_robustness_analysis(df)
        
        # 3. Save report
        output_file = DATA_RESULTS_DIR / "robustness_report.json"
        save_report(report, output_file)
        
        logger.info("T027b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T027b: {e}")
        raise

if __name__ == "__main__":
    main()
