import os
import json
import logging
import argparse
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from code.config import SEED, OUTLIER_SIGMA, VIF_THRESHOLD, TARGET_VAR
from code.data_loader import load_processed_data
from code.scaffold_split import scaffold_split
from code.model_training import train_models
from code.outlier_utils import apply_threshold_filter
from code.vif_analysis import calculate_vif, get_high_vif_features

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def filter_outliers(df, target_col, sigma_threshold):
    """
    Filter rows based on z-score threshold for the target column.
    
    Args:
        df (pd.DataFrame): Input DataFrame.
        target_col (str): Name of the target column.
        sigma_threshold (float): Z-score threshold for outlier removal.
        
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    
    mean_val = df[target_col].mean()
    std_val = df[target_col].std()
    
    if std_val == 0:
        logger.warning(f"Standard deviation of {target_col} is 0. No outliers to filter.")
        return df
    
    z_scores = np.abs((df[target_col] - mean_val) / std_val)
    filtered_df = df[z_scores <= sigma_threshold]
    
    dropped_count = len(df) - len(filtered_df)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows due to outlier threshold {sigma_threshold}.")
    
    return filtered_df

def calculate_vif(X, feature_names):
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        X (np.ndarray): Feature matrix.
        feature_names (list): List of feature names.
        
    Returns:
        dict: Mapping of feature names to VIF scores.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    if X.shape[0] < X.shape[1] + 1:
        logger.warning("Not enough samples for VIF calculation. Returning NaN for all.")
        return {name: np.nan for name in feature_names}
    
    vif_data = {}
    for i, name in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data[name] = vif
        except Exception as e:
            logger.warning(f"VIF calculation failed for {name}: {e}")
            vif_data[name] = np.nan
    
    return vif_data

def exclude_high_vif_features(vif_scores, threshold):
    """
    Identify features with VIF above the threshold.
    
    Args:
        vif_scores (dict): VIF scores for features.
        threshold (float): VIF threshold.
        
    Returns:
        list: List of feature names to exclude.
    """
    return [name for name, score in vif_scores.items() if score > threshold]

def train_and_evaluate_model(X_train, y_train, X_test, y_test, model_type='rf'):
    """
    Train a model and evaluate on test set.
    
    Args:
        X_train (np.ndarray): Training features.
        y_train (np.ndarray): Training target.
        X_test (np.ndarray): Test features.
        y_test (np.ndarray): Test target.
        model_type (str): 'rf' or 'gb'.
        
    Returns:
        dict: Evaluation metrics (r2, mae).
    """
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.metrics import r2_score, mean_absolute_error
    from code.config import SEED
    
    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
    elif model_type == 'gb':
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    return {
        'r2': r2_score(y_test, y_pred),
        'mae': mean_absolute_error(y_test, y_pred)
    }

def run_vif_iterative_loop(df, target_col, feature_cols, thresholds=[2.5, 3.0, 3.5], vif_threshold=10):
    """
    Run iterative VIF filtering and model retraining.
    
    Args:
        df (pd.DataFrame): Input DataFrame.
        target_col (str): Target column name.
        feature_cols (list): List of feature column names.
        thresholds (list): List of outlier thresholds for sensitivity analysis.
        vif_threshold (float): VIF threshold for exclusion.
        
    Returns:
        dict: VIF iteration log.
    """
    log = {'iterations': []}
    current_features = feature_cols.copy()
    
    for iteration in range(100):  # Safety limit
        if not current_features:
            logger.critical("Feature set became empty. Halting VIF loop.")
            break
        
        X = df[current_features].values
        y = df[target_col].values
        
        # Split data
        train_idx, test_idx = scaffold_split(df, current_features, target_col)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Calculate VIF
        vif_scores = calculate_vif(X_train, current_features)
        high_vif = exclude_high_vif_features(vif_scores, vif_threshold)
        
        if not high_vif:
            logger.info(f"VIF loop converged at iteration {iteration}.")
            break
        
        # Exclude highest VIF feature
        worst_feature = max(high_vif, key=lambda k: vif_scores[k])
        current_features.remove(worst_feature)
        
        # Retrain model
        metrics = train_and_evaluate_model(X_train, y_train, X_test, y_test)
        
        log['iterations'].append({
            'iteration': iteration + 1,
            'excluded_feature': worst_feature,
            'vif_scores': vif_scores,
            'r2': metrics['r2'],
            'mae': metrics['mae']
        })
        
        logger.info(f"Iteration {iteration + 1}: Excluded {worst_feature}, R2={metrics['r2']:.4f}")
    
    return log

def update_model_results(results_path, new_results):
    """
    Update the model results JSON file.
    
    Args:
        results_path (str): Path to results JSON.
        new_results (dict): New results to merge.
    """
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    data.update(new_results)
    
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Updated model results at {results_path}")

def apply_bh_correction(p_values, feature_names):
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values (list): List of raw p-values.
        feature_names (list): List of corresponding feature names.
        
    Returns:
        dict: Mapping of feature names to adjusted p-values.
    """
    if len(p_values) == 0:
        return {}
    
    try:
        # multipletests returns (reject, pvals_corrected, alphacSidak, alphacBonf)
        _, pvals_corrected, _, _ = multipletests(p_values, method='fdr_bh')
    except Exception as e:
        logger.error(f"Benjamini-Hochberg correction failed: {e}")
        raise
    
    return {name: float(p) for name, p in zip(feature_names, pvals_corrected)}

def main():
    parser = argparse.ArgumentParser(description="Run analysis pipeline including FDR correction.")
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv', help='Path to processed data')
    parser.add_argument('--target', type=str, default=TARGET_VAR, help='Target variable name')
    parser.add_argument('--results', type=str, default='data/processed/model_results.json', help='Path to model results')
    parser.add_argument('--plots', type=str, default='data/processed/correlation_plots/', help='Directory for plots')
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)
    
    if df is None or df.empty:
        logger.error("No data loaded. Exiting.")
        sys.exit(1)
    
    # Identify target and features
    target_col = args.target
    if target_col not in df.columns:
        # Fallback logic if target not found (e.g., HOMO-LUMO)
        if 'HOMO_LUMO_gap' in df.columns:
            target_col = 'HOMO_LUMO_gap'
            logger.warning(f"Target '{args.target}' not found. Using HOMO_LUMO_gap as proxy.")
        else:
            logger.error(f"Neither '{args.target}' nor 'HOMO_LUMO_gap' found in data.")
            sys.exit(1)
    
    feature_cols = [col for col in df.columns if col not in ['smiles', 'valid', 'error_msg', target_col]]
    
    # Calculate correlations and p-values (assuming this was done in T041)
    # We need to compute them here if not saved, or load them.
    # For this task, we assume T041 saved correlation results or we compute them.
    # Let's compute them here to ensure independence.
    from scipy.stats import pearsonr
    
    p_values = []
    feature_names = []
    
    for feat in feature_cols:
        if feat in df.columns and target_col in df.columns:
            # Drop NaNs for correlation
            valid_mask = df[[feat, target_col]].notna().all(axis=1)
            if valid_mask.sum() > 1:
                corr, p_val = pearsonr(df.loc[valid_mask, feat], df.loc[valid_mask, target_col])
                p_values.append(p_val)
                feature_names.append(feat)
            else:
                p_values.append(1.0) # Not significant
                feature_names.append(feat)
        else:
            p_values.append(1.0)
            feature_names.append(feat)
    
    # Apply Benjamini-Hochberg correction
    logger.info("Applying Benjamini-Hochberg FDR correction.")
    adjusted_p_values = apply_bh_correction(p_values, feature_names)
    
    # Save adjusted p-values to a temporary file or update model_results
    # The task T042 specifically asks for the output format: dictionary mapping feature names to adjusted p-values.
    # We will save this to the model_results.json as 'fdr_corrected_p_values'
    
    fdr_data = {
        'fdr_method': 'fdr_bh',
        'adjusted_p_values': adjusted_p_values
    }
    
    update_model_results(args.results, fdr_data)
    
    logger.info(f"Benjamini-Hochberg correction complete. Results saved to {args.results}")
    
    return adjusted_p_values

if __name__ == '__main__':
    import sys
    main()