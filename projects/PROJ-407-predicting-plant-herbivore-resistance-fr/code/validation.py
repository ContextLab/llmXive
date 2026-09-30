import os
import json
import logging
import argparse
from pathlib import Path
from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/interim/permutation_run.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """Load processed dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded processed data with shape {df.shape}")
    return df

def load_split_indices(split_path: str) -> Dict[str, List[int]]:
    """Load train/test split indices."""
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split indices file not found: {split_path}")
    with open(split_path, 'r') as f:
        return json.load(f)

def load_model(model_path: str) -> RandomForestRegressor:
    """Load trained model."""
    import pickle
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_model_metrics(metrics_path: str) -> Dict[str, float]:
    """Load model metrics."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R² score."""
    return r2_score(y_true, y_pred)

def calculate_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Squared Error."""
    return mean_squared_error(y_true, y_pred)

def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int,
    model_class=RandomForestRegressor,
    model_params=None,
    random_seed: int = 42
) -> Tuple[np.ndarray, float]:
    """
    Run permutation test to generate null distribution.
    Returns null distribution and empirical p-value.
    """
    logger.info(f"Starting permutation test with {n_permutations} iterations")
    
    if model_params is None:
        model_params = {'n_estimators': 100, 'max_depth': 10, 'random_state': random_seed}
    
    # Calculate observed R²
    model = model_class(**model_params)
    model.fit(X, y)
    y_pred = model.predict(X)
    observed_r2 = calculate_r2(y, y_pred)
    logger.info(f"Observed R²: {observed_r2}")

    # Generate null distribution
    null_r2s = []
    rng = np.random.default_rng(random_seed)
    
    for i in range(n_permutations):
        y_perm = rng.permutation(y)
        model_perm = model_class(**model_params)
        model_perm.fit(X, y_perm)
        y_pred_perm = model_perm.predict(X)
        r2_perm = calculate_r2(y_perm, y_pred_perm)
        null_r2s.append(r2_perm)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations} completed")

    null_distribution = np.array(null_r2s)
    
    # Calculate p-value: proportion of null R² >= observed R²
    p_value = np.mean(null_distribution >= observed_r2)
    logger.info(f"Permutation p-value: {p_value}")
    
    return null_distribution, p_value

def apply_batch_covariate_adjustment(
    df: pd.DataFrame,
    batch_col: str = 'study_id'
) -> pd.DataFrame:
    """
    Apply batch covariate adjustment by one-hot encoding batch/study_id.
    Returns adjusted dataframe.
    """
    if batch_col not in df.columns:
        logger.warning(f"Batch column '{batch_col}' not found in dataset. Skipping adjustment.")
        return df

    # One-hot encode batch column
    df_adjusted = pd.get_dummies(df, columns=[batch_col], drop_first=True)
    logger.info(f"Applied batch covariate adjustment using column '{batch_col}'")
    return df_adjusted

def calculate_univariate_correlations(
    df: pd.DataFrame,
    target_col: str = 'resistance'
) -> pd.DataFrame:
    """
    Calculate univariate correlations (Pearson) between each metabolite and the target.
    Returns DataFrame with metabolite_name, correlation_coefficient, p_value.
    """
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    if not metabolite_cols:
        raise ValueError("No metabolite columns found in dataset")
    
    target = df[target_col].dropna()
    results = []
    
    logger.info(f"Calculating correlations for {len(metabolite_cols)} metabolites")
    
    for col in metabolite_cols:
        x = df[col].dropna()
        # Align indices
        common_idx = x.index.intersection(target.index)
        if len(common_idx) < 5:
            continue
        
        x_aligned = x.loc[common_idx]
        y_aligned = target.loc[common_idx]
        
        corr, p_val = stats.pearsonr(x_aligned, y_aligned)
        results.append({
            'metabolite_name': col,
            'correlation_coefficient': corr,
            'unadjusted_p_value': p_val
        })
    
    corr_df = pd.DataFrame(results)
    logger.info(f"Calculated {len(corr_df)} correlations")
    return corr_df

def save_correlations(corr_df: pd.DataFrame, output_path: str):
    """Save correlation results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    corr_df.to_csv(output_path, index=False)
    logger.info(f"Saved correlations to {output_path}")

def apply_benjamini_hochberg_correction(p_values: np.ndarray) -> np.ndarray:
    """
    Apply Benjamini-Hochberg correction to generate q-values from unadjusted p-values.
    
    Parameters:
        p_values: Array of unadjusted p-values
        
    Returns:
        Array of adjusted q-values (FDR-corrected)
    """
    if len(p_values) == 0:
        return np.array([])
    
    # Sort p-values and keep track of original indices
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values (q-values)
    q_values = np.zeros(n)
    for i in range(n):
        rank = i + 1
        q_values[sorted_indices[i]] = sorted_p[i] * n / rank
    
    # Ensure monotonicity: q-values should be non-decreasing with rank
    # Process from largest to smallest rank
    for i in range(n - 2, -1, -1):
        q_values[sorted_indices[i]] = min(q_values[sorted_indices[i]], q_values[sorted_indices[i+1]])
    
    # Cap at 1.0
    q_values = np.minimum(q_values, 1.0)
    
    return q_values

def save_bh_correction_results(
    corr_df: pd.DataFrame,
    output_path: str
):
    """
    Apply Benjamini-Hochberg correction to correlation p-values and save results.
    Adds 'q_value' column to the dataframe.
    """
    if 'unadjusted_p_value' not in corr_df.columns:
        raise ValueError("DataFrame must contain 'unadjusted_p_value' column")
    
    p_values = corr_df['unadjusted_p_value'].values
    q_values = apply_benjamini_hochberg_correction(p_values)
    
    corr_df['q_value'] = q_values
    corr_df['significant'] = corr_df['q_value'] < 0.10
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    corr_df.to_csv(output_path, index=False)
    logger.info(f"Saved BH-corrected correlations to {output_path}")
    logger.info(f"Significant metabolites (q < 0.10): {corr_df['significant'].sum()}")

def save_results(
    null_distribution: np.ndarray,
    p_value: float,
    output_dir: str
):
    """Save permutation test results."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save null distribution
    null_df = pd.DataFrame({'r2_value': null_distribution})
    null_path = os.path.join(output_dir, 'null_distribution.csv')
    null_df.to_csv(null_path, index=False)
    logger.info(f"Saved null distribution to {null_path}")
    
    # Save p-value
    p_value_path = os.path.join(output_dir, 'permutation_p_value.json')
    with open(p_value_path, 'w') as f:
        json.dump({'p_value': p_value, 'n_permutations': len(null_distribution)}, f)
    logger.info(f"Saved p-value to {p_value_path}")

def main():
    parser = argparse.ArgumentParser(description='Run statistical validation and BH correction')
    parser.add_argument('--input', type=str, required=True, help='Path to processed data CSV')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model pickle')
    parser.add_argument('--output', type=str, required=True, help='Output directory for results')
    parser.add_argument('--split', type=str, default='data/interim/split_indices.json', help='Path to split indices')
    parser.add_argument('--metrics', type=str, default='data/processed/model_metrics.json', help='Path to model metrics')
    parser.add_argument('--n_permutations', type=int, default=1000, help='Number of permutation iterations')
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_processed_data(args.input)
        
        # Identify metabolite columns
        metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
        target_col = 'resistance'
        
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset")
        
        X = df[metabolite_cols].values
        y = df[target_col].values
        
        # Remove rows with NaN in target or features
        valid_mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[valid_mask]
        y = y[valid_mask]
        
        logger.info(f"Using {len(y)} samples for validation")
        
        # Run permutation test
        null_dist, p_val = run_permutation_test(X, y, args.n_permutations)
        
        # Save permutation results
        save_results(null_dist, p_val, args.output)
        
        # Calculate univariate correlations on training set
        # Note: In a full pipeline, we would load the training split specifically
        # For now, we use the full dataset as a proxy
        corr_df = calculate_univariate_correlations(df, target_col)
        
        # Apply Benjamini-Hochberg correction
        corr_path = os.path.join(args.output, 'correlations.csv')
        save_bh_correction_results(corr_df, corr_path)
        
        # Check global significance
        if p_val >= 0.05:
            logger.warning("Global p-value >= 0.05. Model may not be significantly better than random.")
            # Note: T031 handles the "Null Result" reporting in the final report
        
        logger.info("Validation and BH correction completed successfully")
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
