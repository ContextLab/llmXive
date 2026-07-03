import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from scipy import stats

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import set_all_seeds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_flexibility_scores(file_path: str = "data/processed/flexibility_scores.parquet") -> pd.DataFrame:
    """
    Load flexibility scores from the processed Parquet file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Flexibility scores file not found: {path}")
    
    df = pd.read_parquet(path)
    logger.info(f"Loaded flexibility scores for {len(df)} subjects from {path}")
    return df

def load_behavioral_scores(file_path: str = "data/processed/consolidated_data.parquet") -> pd.DataFrame:
    """
    Load behavioral scores (2-back accuracy) from the consolidated Parquet file.
    Expects a 'accuracy' or '2back_accuracy' column.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Behavioral scores file not found: {path}")
    
    df = pd.read_parquet(path)
    
    # Identify the accuracy column
    acc_col = None
    for col in ['accuracy', '2back_accuracy', 'nback_accuracy']:
        if col in df.columns:
            acc_col = col
            break
    
    if acc_col is None:
        raise ValueError("Could not find accuracy column in behavioral data. Columns: " + str(df.columns.tolist()))
    
    logger.info(f"Loaded behavioral scores ({acc_col}) for {len(df)} subjects from {path}")
    return df[[ 'subject_id', acc_col ]]

def merge_analysis_data(flex_df: pd.DataFrame, behav_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge flexibility scores and behavioral scores on subject_id.
    """
    # Ensure subject_id is consistent type
    if 'subject_id' in flex_df.columns:
        flex_df = flex_df.copy()
        flex_df['subject_id'] = flex_df['subject_id'].astype(str)
    
    if 'subject_id' in behav_df.columns:
        behav_df = behav_df.copy()
        behav_df['subject_id'] = behav_df['subject_id'].astype(str)

    merged = pd.merge(flex_df, behav_df, on='subject_id', how='inner')
    logger.info(f"Merged data contains {len(merged)} subjects after inner join.")
    return merged

def compute_partial_spearman_correlation(data: pd.DataFrame, 
                                         x_col: str = 'flexibility_score', 
                                         y_col: str = 'accuracy', 
                                         control_cols: List[str] = None) -> Tuple[float, float]:
    """
    Compute partial Spearman correlation between x and y, controlling for control_cols.
    Uses scipy.stats.spearmanr for the base correlation and residuals for partial.
    
    Returns:
        (rho, p_value)
    """
    if control_cols is None:
        control_cols = []
    
    # Filter out rows with NaN in relevant columns
    cols_to_check = [x_col, y_col] + control_cols
    clean_data = data[cols_to_check].dropna()
    
    if len(clean_data) < 10:
        raise ValueError(f"Not enough data points ({len(clean_data)}) to compute partial correlation.")
    
    x = clean_data[x_col].values
    y = clean_data[y_col].values
    
    if len(control_cols) > 0:
        Z = clean_data[control_cols].values
        
        # Rank transform for Spearman (partial correlation on ranks)
        x_rank = stats.rankdata(x)
        y_rank = stats.rankdata(y)
        Z_rank = np.apply_along_axis(stats.rankdata, 0, Z)
        
        # Compute residuals of x and y against Z (linear regression)
        # Using least squares: residuals = y - X @ beta
        # Add intercept
        Z_aug = np.c_[np.ones(len(Z_rank)), Z_rank]
        
        # Solve for x residuals
        try:
            beta_x, _, _, _ = np.linalg.lstsq(Z_aug, x_rank, rcond=None)
            x_resid = x_rank - Z_aug @ beta_x
            
            beta_y, _, _, _ = np.linalg.lstsq(Z_aug, y_rank, rcond=None)
            y_resid = y_rank - Z_aug @ beta_y
        except np.linalg.LinAlgError:
            logger.warning("Singular matrix in partial correlation control. Proceeding without control.")
            x_resid = x_rank
            y_resid = y_rank
    else:
        x_resid = stats.rankdata(x)
        y_resid = stats.rankdata(y)
    
    rho, p_val = stats.spearmanr(x_resid, y_resid)
    logger.info(f"Partial Spearman correlation: rho={rho:.4f}, p={p_val:.4f}")
    return rho, p_val

def run_permutation_test(data: pd.DataFrame, 
                         x_col: str = 'flexibility_score', 
                         y_col: str = 'accuracy', 
                         control_cols: List[str] = None,
                         n_permutations: int = 1000,
                         random_seed: int = 42) -> Dict[str, Any]:
    """
    Run a non-parametric permutation test for the partial correlation.
    
    Strategy:
    1. Compute observed partial Spearman correlation (rho_obs).
    2. Permute the Y variable (behavioral scores) relative to X and controls.
    3. Recompute partial correlation for each permutation.
    4. Calculate p-value as (count(|rho_perm| >= |rho_obs|) + 1) / (n_permutations + 1).
    
    This controls for discrete sampling by including the observed statistic in the null distribution.
    """
    set_all_seeds(random_seed)
    
    # Prepare clean data
    cols_to_check = [x_col, y_col] + (control_cols if control_cols else [])
    clean_data = data[cols_to_check].dropna()
    
    if len(clean_data) < 10:
        raise ValueError(f"Insufficient data for permutation test: {len(clean_data)} rows.")
    
    x = clean_data[x_col].values
    y = clean_data[y_col].values
    Z = clean_data[control_cols].values if control_cols else None
    
    # Helper to compute partial correlation on arrays
    def compute_partial_rho(x_arr, y_arr, Z_arr):
        if Z_arr is not None and Z_arr.shape[1] > 0:
            x_rank = stats.rankdata(x_arr)
            y_rank = stats.rankdata(y_arr)
            Z_rank = np.apply_along_axis(stats.rankdata, 0, Z_arr)
            
            Z_aug = np.c_[np.ones(len(Z_rank)), Z_rank]
            try:
                beta_x, _, _, _ = np.linalg.lstsq(Z_aug, x_rank, rcond=None)
                x_resid = x_rank - Z_aug @ beta_x
                
                beta_y, _, _, _ = np.linalg.lstsq(Z_aug, y_rank, rcond=None)
                y_resid = y_rank - Z_aug @ beta_y
            except np.linalg.LinAlgError:
                return 0.0
        else:
            x_resid = stats.rankdata(x_arr)
            y_resid = stats.rankdata(y_arr)
        
        rho, _ = stats.spearmanr(x_resid, y_resid)
        return rho

    # Observed statistic
    rho_obs = compute_partial_rho(x, y, Z)
    logger.info(f"Observed partial Spearman rho: {rho_obs:.4f}")
    
    # Permutation loop
    perm_rhos = np.zeros(n_permutations)
    n = len(x)
    
    for i in range(n_permutations):
        # Permute Y
        y_perm = np.random.permutation(y)
        perm_rhos[i] = compute_partial_rho(x, y_perm, Z)
    
    # Calculate p-value (two-tailed)
    # Include observed in the count to avoid p=0 (discrete sampling correction)
    abs_obs = np.abs(rho_obs)
    abs_perms = np.abs(perm_rhos)
    
    count_extreme = np.sum(abs_perms >= abs_obs)
    p_value = (count_extreme + 1) / (n_permutations + 1)
    
    logger.info(f"Permutation test completed. N={n_permutations}, p={p_value:.4f}")
    
    return {
        "observed_rho": float(rho_obs),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "n_subjects": n,
        "null_distribution": perm_rhos.tolist(), # Save for plotting
        "control_variables": control_cols if control_cols else []
    }

def save_results(results: Dict[str, Any], output_path: str = "data/results/statistical_report.json"):
    """
    Save statistical results to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {path}")

def main():
    """
    Main entry point to run the permutation test on the project data.
    """
    logger.info("Starting T026: Permutation Test Implementation")
    
    try:
        # 1. Load Data
        flex_df = load_flexibility_scores()
        behav_df = load_behavioral_scores()
        
        # 2. Merge
        merged_data = merge_analysis_data(flex_df, behav_df)
        
        # 3. Define Control Variables (Mean FD is standard for motion control)
        # Check if mean_fd is in the merged data (from preprocessing)
        control_vars = []
        if 'mean_fd' in merged_data.columns:
            control_vars = ['mean_fd']
            logger.info("Using mean_fd as control variable for motion.")
        else:
            logger.warning("mean_fd not found in merged data. Running without motion control.")
        
        # 4. Run Permutation Test
        results = run_permutation_test(
            data=merged_data,
            x_col='flexibility_score', # Assuming column name from US2
            y_col='accuracy',          # Assuming column name from US1
            control_cols=control_vars,
            n_permutations=1000,
            random_seed=42
        )
        
        # 5. Save Results
        save_results(results)
        
        logger.info("T026 Permutation Test completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T026 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()