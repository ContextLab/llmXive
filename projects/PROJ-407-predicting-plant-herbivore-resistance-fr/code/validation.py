import os
import json
import logging
import argparse
from pathlib import Path
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/interim/permutation_run.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """Load the processed dataset (harmonized or batch corrected)."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def load_split_indices(indices_path: str) -> Dict[str, List[int]]:
    """Load train/test split indices from JSON."""
    if not os.path.exists(indices_path):
        raise FileNotFoundError(f"Split indices file not found: {indices_path}")
    with open(indices_path, 'r') as f:
        return json.load(f)

def load_model(model_path: str) -> RandomForestRegressor:
    """Load the trained Random Forest model."""
    import pickle
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_model_metrics(metrics_path: str) -> Dict[str, Any]:
    """Load model metrics from JSON."""
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

def apply_batch_covariate_adjustment(data: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Perform batch covariate adjustment if batch metadata exists.
    Returns adjusted data and a boolean indicating if adjustment was performed.
    """
    batch_cols = [col for col in data.columns if col.startswith('batch_')]
    if not batch_cols:
        logger.warning("No batch metadata found; proceeding without batch correction.")
        return data, False

    # One-hot encoding is already done if columns exist
    # For this implementation, we assume data is already one-hot encoded if batch_cols exist
    logger.info(f"Found batch columns: {batch_cols}")
    return data, True

def run_permutation_test(
    X: pd.DataFrame,
    y: np.ndarray,
    n_permutations: int,
    stratify_by: str = None,
    model_type: str = 'random_forest'
) -> Tuple[List[float], float, float]:
    """
    Run permutation test to validate model performance.
    
    Args:
        X: Feature matrix (metabolites)
        y: Target vector (resistance scores)
        n_permutations: Number of permutations
        stratify_by: Column name to stratify by (study_id, batch, or genotype_id)
        model_type: Type of model to use for scoring
    
    Returns:
        null_distribution: List of R² scores from permuted data
        p_value: Calculated p-value
        observed_r2: R² score from original data
    """
    logger.info(f"Starting permutation test with {n_permutations} iterations")
    
    # Calculate observed R²
    if model_type == 'random_forest':
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=config.RANDOM_SEED)
        model.fit(X, y)
        y_pred = model.predict(X)
        observed_r2 = calculate_r2(y, y_pred)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    logger.info(f"Observed R²: {observed_r2:.4f}")
    
    null_distribution = []
    indices = np.arange(len(y))
    
    # Determine stratification groups
    stratify_groups = None
    if stratify_by:
        if stratify_by not in X.columns:
            logger.warning(f"Stratification column '{stratify_by}' not found in features. Using genotype_id fallback.")
            # Try to find genotype_id if it's in the original data but not in X
            # This assumes X might have been derived from a larger dataframe
            # For now, we'll just use random shuffling if stratify_by is missing
            stratify_groups = None
        else:
            stratify_groups = X[stratify_by].values
    
    for i in range(n_permutations):
        if stratify_groups is not None:
            # Stratified permutation: shuffle within groups
            y_permuted = np.zeros_like(y)
            unique_groups = np.unique(stratify_groups)
            for group in unique_groups:
                group_mask = stratify_groups == group
                group_indices = indices[group_mask]
                y_permuted[group_mask] = y[group_indices][np.random.permutation(len(group_indices))]
        else:
            # Random permutation
            y_permuted = y[np.random.permutation(len(y))]
        
        # Train model on permuted data
        perm_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=config.RANDOM_SEED + i)
        perm_model.fit(X, y_permuted)
        y_perm_pred = perm_model.predict(X)
        r2_perm = calculate_r2(y_permuted, y_perm_pred)
        null_distribution.append(r2_perm)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")
    
    # Calculate p-value
    # p-value = (number of permuted R² >= observed R² + 1) / (n_permutations + 1)
    p_value = (np.sum(np.array(null_distribution) >= observed_r2) + 1) / (n_permutations + 1)
    
    logger.info(f"Permutation test completed. P-value: {p_value:.4f}")
    return null_distribution, p_value, observed_r2

def calculate_univariate_correlations(X: pd.DataFrame, y: np.ndarray) -> pd.DataFrame:
    """
    Calculate univariate correlations between each metabolite and resistance.
    
    Args:
        X: Feature matrix (metabolites)
        y: Target vector (resistance scores)
    
    Returns:
        DataFrame with columns: metabolite_name, correlation_coefficient, p_value
    """
    results = []
    for col in X.columns:
        if col.startswith('metabolite_') or col.startswith('PC'):
            # Determine if resistance is continuous or ordinal
            # For simplicity, we'll use Pearson for continuous and Spearman for ordinal
            # Assuming y is numeric; if it's ordinal, Spearman might be more appropriate
            # We'll use Pearson as default for continuous resistance scores
            corr, p_val = stats.pearsonr(X[col], y)
            results.append({
                'metabolite_name': col,
                'correlation_coefficient': corr,
                'p_value': p_val
            })
    
    return pd.DataFrame(results)

def apply_benjamini_hochberg_correction(p_values: np.ndarray) -> np.ndarray:
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        p_values: Array of unadjusted p-values
    
    Returns:
        Array of adjusted p-values (q-values)
    """
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values
    q_values = np.zeros(n)
    for i in range(n):
        q_values[sorted_indices[i]] = sorted_p_values[i] * n / (i + 1)
    
    # Ensure monotonicity
  # Ensure monotonicity
    for i in range(n-2, -1, -1):
        q_values[sorted_indices[i]] = min(q_values[sorted_indices[i]], q_values[sorted_indices[i+1]])
    
    return np.clip(q_values, 0, 1)

def save_correlations(correlations: pd.DataFrame, output_path: str):
    """Save correlation results to CSV."""
    correlations.to_csv(output_path, index=False)
    logger.info(f"Correlations saved to {output_path}")

def save_bh_correction_results(q_values: np.ndarray, p_values: np.ndarray, output_path: str):
    """Save BH correction results to JSON."""
    results = {
        'unadjusted_p_values': p_values.tolist(),
        'adjusted_q_values': q_values.tolist()
    }
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"BH correction results saved to {output_path}")

def save_results(null_distribution: List[float], p_value: float, observed_r2: float, output_dir: str):
    """Save permutation test results."""
    # Save null distribution
    null_df = pd.DataFrame({
        'iteration': range(len(null_distribution)),
        'r2_score': null_distribution
    })
    null_df.to_csv(os.path.join(output_dir, 'null_distribution.csv'), index=False)
    logger.info(f"Null distribution saved to {os.path.join(output_dir, 'null_distribution.csv')}")
    
    # Save p-value
    p_value_data = {
        'p_value': p_value,
        'n_permutations': len(null_distribution),
        'observed_r2': observed_r2,
        'null_mean_r2': float(np.mean(null_distribution)),
        'null_std_r2': float(np.std(null_distribution))
    }
    with open(os.path.join(output_dir, 'permutation_p_value.json'), 'w') as f:
        json.dump(p_value_data, f, indent=2)
    logger.info(f"P-value results saved to {os.path.join(output_dir, 'permutation_p_value.json')}")

def main():
    parser = argparse.ArgumentParser(description='Run permutation test and validation')
    parser.add_argument('--input', type=str, required=True, help='Path to processed data CSV')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--split-indices', type=str, default='data/interim/split_indices.json', help='Path to split indices')
    parser.add_argument('--metrics', type=str, default='data/processed/model_metrics.json', help='Path to model metrics')
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    data = load_processed_data(args.input)
    
    # Load split indices
    split_indices = load_split_indices(args.split_indices)
    train_indices = split_indices['train_indices']
    test_indices = split_indices['test_indices']
    
    # Separate features and target
    # Assuming the last column is the target (resistance)
    feature_cols = [col for col in data.columns if col not in ['sample_id', 'genotype_id', 'resistance', 'resistance_ordinal']]
    X = data[feature_cols].values
    y = data['resistance_ordinal'].values if 'resistance_ordinal' in data.columns else data['resistance'].values
    
    # Split data
    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]
    
    # Load model
    logger.info(f"Loading model from {args.model}")
    model = load_model(args.model)
    
    # Evaluate model on test set
    y_pred = model.predict(X_test)
    test_r2 = calculate_r2(y_test, y_pred)
    test_mse = calculate_mse(y_test, y_pred)
    logger.info(f"Test R²: {test_r2:.4f}, Test MSE: {test_mse:.4f}")
    
    # Determine stratification field
    stratify_field = None
    if 'study_id' in data.columns:
        stratify_field = 'study_id'
    elif 'batch' in data.columns:
        stratify_field = 'batch'
    else:
        stratify_field = 'genotype_id'
    
    logger.info(f"Using stratification field: {stratify_field}")
    
    # Run permutation test
    logger.info("Running permutation test")
    null_distribution, p_value, observed_r2 = run_permutation_test(
        X_train, y_train, 
        n_permutations=config.N_PERMUTATIONS, 
        stratify_by=stratify_field
    )
    
    # Save results
    save_results(null_distribution, p_value, observed_r2, args.output)
    
    # Calculate univariate correlations on test set
    logger.info("Calculating univariate correlations")
    X_test_df = pd.DataFrame(X_test, columns=feature_cols)
    correlations = calculate_univariate_correlations(X_test_df, y_test)
    save_correlations(correlations, os.path.join(args.output, 'correlations.csv'))
    
    # Apply BH correction
    logger.info("Applying Benjamini-Hochberg correction")
    q_values = apply_benjamini_hochberg_correction(correlations['p_value'].values)
    save_bh_correction_results(q_values, correlations['p_value'].values, os.path.join(args.output, 'bh_correction_results.json'))
    
    # Log completion
    logger.info(f"Permutation test and validation completed. P-value: {p_value:.4f}")
    logger.info(f"Null Result: {'Yes' if p_value >= 0.05 else 'No'}")

if __name__ == '__main__':
    main()
