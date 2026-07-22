"""
Sensitivity Analysis Generator (T039a).

Generates data/final/sensitivity_analysis.csv from the intermediate results
produced by the sensitivity analysis loop in T044.

This script aggregates the results of re-running the matching and modeling
pipeline with different Levenshtein thresholds to assess the stability of
the primary findings.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger

# Configure logging
logger = setup_logging()

# Constants
THRESHOLD_RANGE = [2, 3, 4, 5, 6]
INTERMEDIATE_DIR = "data/processed"
FINAL_DIR = "data/final"
OUTPUT_FILE = "sensitivity_analysis.csv"
TEMP_SUFFIX = "_threshold_"

def load_sensitivity_intermediate_results(threshold: int) -> Optional[pd.DataFrame]:
    """
    Load the regression results for a specific threshold from T044.
    
    Args:
        threshold: The Levenshtein threshold used for this iteration.
        
    Returns:
        DataFrame with model coefficients, or None if file not found.
    """
    root = get_project_root()
    # The intermediate file naming convention from T044:
    # data/processed/user_track_pairs_threshold_X.parquet
    # However, T044 also needs to produce a regression summary for each.
    # Based on T038 logic, the regression summary is typically in data/final.
    # But for sensitivity analysis, we need the specific run's results.
    # We will assume T044 produced a CSV in the intermediate folder or
    # we reconstruct from the parquet if T044 stored the model stats.
    
    # Let's assume T044 writes a temporary regression summary per threshold
    # in the processed folder to avoid overwriting the main one.
    # Pattern: data/processed/regression_summary_threshold_X.csv
    
    file_path = root / INTERMEDIATE_DIR / f"regression_summary_threshold_{threshold}.csv"
    
    if not file_path.exists():
        # Fallback: try to load the parquet and re-run a quick model?
        # No, T044 should have saved the results. If not, we fail loudly.
        logger.warning(f"Intermediate regression summary for threshold {threshold} not found: {file_path}")
        return None
        
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logger.error(f"Error loading intermediate results for threshold {threshold}: {e}")
        return None

def generate_sensitivity_summary(results_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate results from multiple thresholds into a summary table.
    
    Args:
        results_list: List of dictionaries containing model stats per threshold.
        
    Returns:
        DataFrame summarizing the sensitivity analysis.
    """
    if not results_list:
        raise ValueError("No results to summarize. Ensure T044 ran successfully.")
    
    # Expected columns: threshold, coefficient, std_err, p_value, n_obs, n_groups
    data = []
    for res in results_list:
        data.append({
            'threshold': res.get('threshold'),
            'residualized_exposure_coef': res.get('residualized_exposure_coef'),
            'residualized_exposure_se': res.get('residualized_exposure_se'),
            'residualized_exposure_pvalue': res.get('residualized_exposure_pvalue'),
            'popularity_coef': res.get('popularity_coef'),
            'popularity_pvalue': res.get('popularity_pvalue'),
            'n_observations': res.get('n_observations'),
            'n_groups': res.get('n_groups'),
            'log_likelihood': res.get('log_likelihood')
        })
    
    return pd.DataFrame(data)

def save_sensitivity_analysis(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the sensitivity analysis results to CSV.
    
    Args:
        df: Summary DataFrame.
        output_path: Destination path.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write pattern
    temp_path = output_path.with_suffix('.csv.tmp')
    df.to_csv(temp_path, index=False)
    os.replace(temp_path, output_path)
    logger.info(f"Sensitivity analysis saved to {output_path}")

def main() -> int:
    """
    Main entry point for T039a.
    Orchestrates loading intermediate results and generating the final CSV.
    """
    root = get_project_root()
    output_path = root / FINAL_DIR / OUTPUT_FILE
    
    logger.info(f"Starting sensitivity analysis generation for T039a.")
    logger.info(f"Expected output: {output_path}")
    
    results = []
    missing_thresholds = []
    
    for t in THRESHOLD_RANGE:
        logger.info(f"Loading results for threshold {t}...")
        df = load_sensitivity_intermediate_results(t)
        
        if df is None:
            missing_thresholds.append(t)
            continue
        
        # Extract key statistics from the dataframe
        # Assuming the dataframe has columns similar to T038 output
        # We look for the row corresponding to 'residualized_exposure'
        if 'term' in df.columns:
            row = df[df['term'] == 'residualized_exposure'].iloc[0]
            coef = row.get('coef')
            se = row.get('std err')
            pval = row.get('P>|t|')
        elif 'coefficient' in df.columns:
            # Fallback column names
            row = df[df['coefficient'] == 'residualized_exposure'].iloc[0]
            coef = row.get('estimate')
            se = row.get('stderr')
            pval = row.get('pvalue')
        else:
            # Try to infer if it's a flat list of stats
            # If the dataframe is just one row of stats for the whole model
            # We need to handle the case where the CSV structure varies.
            # Let's assume a standard statsmodels summary export format or a custom one.
            # If the CSV has 'term', 'coef', 'pvalue' etc.
            if len(df) > 0:
                # Try to find the exposure row
                exposure_rows = df[df.apply(lambda x: 'exposure' in str(x).lower(), axis=1)]
                if not exposure_rows.empty:
                    row = exposure_rows.iloc[0]
                    # Heuristic for column names
                    coef_col = [c for c in df.columns if 'coef' in c.lower()][0]
                    se_col = [c for c in df.columns if 'se' in c.lower() or 'std' in c.lower()][0]
                    pval_col = [c for c in df.columns if 'pval' in c.lower() or 'p>' in c.lower()][0]
                    coef = row[coef_col]
                    se = row[se_col]
                    pval = row[pval_col]
                else:
                    logger.error(f"Could not identify 'residualized_exposure' row in threshold {t} results.")
                    missing_thresholds.append(t)
                    continue
            else:
                logger.error(f"Empty results for threshold {t}.")
                missing_thresholds.append(t)
                continue
        
        # Extract other stats
        n_obs = df.get('n_obs', df.get('n_observations', 0))
        n_groups = df.get('n_groups', 0)
        ll = df.get('log_likelihood', 0)
        
        # If n_obs is a dataframe column, take the first value
        if isinstance(n_obs, pd.Series): n_obs = n_obs.iloc[0]
        if isinstance(n_groups, pd.Series): n_groups = n_groups.iloc[0]
        if isinstance(ll, pd.Series): ll = ll.iloc[0]
        
        results.append({
            'threshold': t,
            'residualized_exposure_coef': coef,
            'residualized_exposure_se': se,
            'residualized_exposure_pvalue': pval,
            'n_observations': n_obs,
            'n_groups': n_groups,
            'log_likelihood': ll
        })
    
    if missing_thresholds:
        logger.warning(f"Missing results for thresholds: {missing_thresholds}. "
                     "This may indicate T044 did not complete successfully for all thresholds.")
        if not results:
            logger.error("No results found for any threshold. Aborting.")
            return 1
    
    summary_df = generate_sensitivity_summary(results)
    
    try:
        save_sensitivity_analysis(summary_df, output_path)
        logger.info("T039a completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to save sensitivity analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
