import os
import json
import logging
import argparse
import numpy as np
import pandas as pd

from scipy import stats
from statsmodels.stats.multitest import multipletests
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from code.config import SEED, OUTLIER_SIGMA, VIF_THRESHOLD, TARGET_VAR, DATA_PATH, RAW_DATA_PATH
from code.scaffold_split import scaffold_split
from code.data_loader import load_processed_data, load_smiles, validate_target_variable
from code.logging_config import setup_logging

# Configure logging
logger = setup_logging(__name__)

def filter_outliers(df, target_col, sigma_threshold=OUTLIER_SIGMA):
    """
    Filter rows where |z_score| <= sigma_threshold for the target column.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    
    mean = df[target_col].mean()
    std = df[target_col].std()
    
    if std == 0:
        logger.warning(f"Standard deviation of {target_col} is 0. Returning original DataFrame.")
        return df
    
    z_scores = np.abs((df[target_col] - mean) / std)
    filtered_df = df[z_scores <= sigma_threshold].copy()
    dropped_count = len(df) - len(filtered_df)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows due to outlier filtering (threshold={sigma_threshold}).")
    
    return filtered_df

def calculate_vif(X, feature_names):
    """
    Calculate Variance Inflation Factor for each feature.
    Returns a dictionary mapping feature names to VIF scores.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_scores = {}
    for i, name in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(X, i)
            vif_scores[name] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {name}: {e}")
            vif_scores[name] = float('inf')
    
    return vif_scores

def exclude_high_vif_features(vif_scores, threshold=VIF_THRESHOLD):
    """
    Identify features with VIF > threshold.
    Returns list of features to exclude.
    """
    return [name for name, vif in vif_scores.items() if vif > threshold]

def train_and_evaluate_model(X_train, y_train, X_test, y_test, model_type='rf'):
    """
    Train a model and evaluate performance.
    Returns model, r2, mae.
    """
    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
    elif model_type == 'gb':
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    return model, r2, mae

def run_vif_iterative_loop(df, target_col, feature_cols, model_type='rf', threshold=VIF_THRESHOLD):
    """
    Iteratively remove features with VIF > threshold, retrain model, and log results.
    """
    log_data = []
    current_features = list(feature_cols)
    iteration = 0
    
    while True:
        X = df[current_features].values
        y = df[target_col].values
        
        # Split data
        indices = np.arange(len(df))
        train_idx, test_idx = scaffold_split(df, indices, seed=SEED)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Calculate VIF
        vif_scores = calculate_vif(X, current_features)
        high_vif_features = exclude_high_vif_features(vif_scores, threshold)
        
        if not high_vif_features:
            # No high VIF features, final iteration
            model, r2, mae = train_and_evaluate_model(X_train, y_train, X_test, y_test, model_type)
            log_data.append({
                'iteration': iteration,
                'excluded_feature': None,
                'vif_scores': vif_scores,
                'r2': r2,
                'mae': mae,
                'final': True
            })
            break
        
        # Exclude the feature with the HIGHEST VIF
        max_vif_feature = max(high_vif_features, key=lambda f: vif_scores[f])
        current_features.remove(max_vif_feature)
        
        if not current_features:
            logger.critical("Guard Clause: Feature set became empty. Halting VIF loop.")
            break
        
        # Retrain model
        X = df[current_features].values
        train_idx, test_idx = scaffold_split(df, indices, seed=SEED)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model, r2, mae = train_and_evaluate_model(X_train, y_train, X_test, y_test, model_type)
        
        log_data.append({
            'iteration': iteration,
            'excluded_feature': max_vif_feature,
            'vif_scores': vif_scores,
            'r2': r2,
            'mae': mae,
            'final': False
        })
        
        iteration += 1
    
    return log_data, current_features

def update_model_results(results_path, log_data):
    """
    Update model_results.json with final metrics from VIF loop.
    """
    if not log_data:
        logger.error("No log data to update model results.")
        return
    
    final_entry = next((entry for entry in reversed(log_data) if entry['final']), log_data[-1])
    
    results = {
        'rf_r2': final_entry['r2'],
        'gb_r2': 0.0, # Placeholder, logic would need to track GB separately
        'cv_scores': [],
        'sensitivity_analysis': {},
        'vif_scores': final_entry['vif_scores'],
        'vif_iteration_log': log_data,
        'final_features': [entry for entry in log_data if entry['final']][0]['excluded_feature'] if any(e['final'] for e in log_data) else None
    }
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Updated {results_path} with final VIF results.")

def calculate_feature_correlations(df, feature_cols, target_col):
    """
    Calculate Pearson correlation and p-value for each feature against target.
    Returns dictionary: {feature: (correlation, p_value)}
    """
    correlations = {}
    y = df[target_col].values
    
    for col in feature_cols:
        x = df[col].values
        corr, p_val = stats.pearsonr(x, y)
        correlations[col] = (corr, p_val)
    
    return correlations

def apply_bh_correction(p_values_dict):
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    Input: dict mapping feature -> p_value
    Output: dict mapping feature -> adjusted p_value
    """
    features = list(p_values_dict.keys())
    p_values = np.array([p_values_dict[f] for f in features])
    
    # multipletests returns (reject, p_corrected, p_sidak, p_bonf)
    _, p_corrected, _, _ = multipletests(p_values, method='fdr_bh')
    
    adjusted_p_values = {features[i]: p_corrected[i] for i in range(len(features))}
    return adjusted_p_values

def save_correlation_results(correlations, output_path):
    """
    Save correlation results to JSON.
    """
    # Convert tuples to serializable format
    serializable = {k: {'corr': v[0], 'p_value': v[1]} for k, v in correlations.items()}
    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)
    logger.info(f"Saved correlation results to {output_path}")

def load_correlation_results(input_path):
    """
    Load correlation results from JSON.
    Returns dict: {feature: (corr, p_value)}
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    return {k: (v['corr'], v['p_value']) for k, v in data.items()}

def main():
    parser = argparse.ArgumentParser(description="Run analysis pipeline.")
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv', help='Path to processed data')
    parser.add_argument('--results', type=str, default='data/processed/model_results.json', help='Path to model results')
    parser.add_argument('--plots', type=str, default='data/processed/correlation_plots/', help='Directory for plots')
    parser.add_argument('--mode', type=str, choices=['vif', 'importance', 'correlation', 'summary'], default='correlation', help='Mode of operation')
    parser.add_argument('--output', type=str, help='Output file path for specific modes')
    args = parser.parse_args()

    # Load data
    df = pd.read_csv(args.data)
    
    # Identify target variable
    target_col = TARGET_VAR
    if target_col not in df.columns:
        if 'log_' + TARGET_VAR in df.columns:
            target_col = 'log_' + TARGET_VAR
        else:
            logger.error(f"Target variable {TARGET_VAR} not found in data.")
            return

    if args.mode == 'vif':
        feature_cols = [c for c in df.columns if c != target_col and c != 'smiles']
        log_data, final_features = run_vif_iterative_loop(df, target_col, feature_cols)
        update_model_results(args.results, log_data)
        vif_log_path = 'data/processed/vif_iteration_log.json'
        with open(vif_log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        logger.info(f"VIF loop complete. Saved log to {vif_log_path}")

    elif args.mode == 'importance':
        # Load final model features from model_results if available, else use all
        try:
            with open(args.results, 'r') as f:
                results = json.load(f)
            final_features = list(results.get('vif_scores', {}).keys())
        except FileNotFoundError:
            logger.warning("model_results.json not found. Using all features.")
            final_features = [c for c in df.columns if c != target_col and c != 'smiles']
        
        # Ensure we have features
        if not final_features:
            final_features = [c for c in df.columns if c != target_col and c != 'smiles']
        
        X = df[final_features].values
        y = df[target_col].values
        
        # Split data
        indices = np.arange(len(df))
        train_idx, test_idx = scaffold_split(df, indices, seed=SEED)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Train a model (using RF as default)
        model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
        model.fit(X_train, y_train)
        
        # Compute permutation importance
        result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=SEED)
        
        # Create ranked list
        importance_scores = result.importances_mean
        feature_importance = list(zip(final_features, importance_scores))
        
        # Sort: Descending by score, then Alphabetically by name for ties
        feature_importance.sort(key=lambda x: (-x[1], x[0]))
        
        # Save to CSV
        output_df = pd.DataFrame(feature_importance, columns=['feature', 'importance_score'])
        output_df.to_csv(args.output, index=False)
        logger.info(f"Saved feature importance to {args.output}")

    elif args.mode == 'correlation':
        feature_cols = [c for c in df.columns if c != target_col and c != 'smiles']
        correlations = calculate_feature_correlations(df, feature_cols, target_col)
        save_correlation_results(correlations, 'data/processed/correlation_results.json')
        
        # Apply BH correction if requested or by default for T042
        p_values = {k: v[1] for k, v in correlations.items()}
        adjusted_p_values = apply_bh_correction(p_values)
        
        # Save adjusted p-values
        adjusted_path = 'data/processed/adjusted_p_values.json'
        with open(adjusted_path, 'w') as f:
            json.dump(adjusted_p_values, f, indent=2)
        logger.info(f"Saved adjusted p-values to {adjusted_path}")

    elif args.mode == 'summary':
        # Load feature importance
        importance_df = pd.read_csv('data/processed/feature_importance.csv')
        top_features = importance_df['feature'].head(5).tolist()
        
        # Load adjusted p-values
        with open('data/processed/adjusted_p_values.json', 'r') as f:
            adjusted_p_values = json.load(f)
        
        # Generate summary
        summary = {
            'top_5_features': top_features,
            'adjusted_p_values': {k: adjusted_p_values.get(k, None) for k in top_features},
            'fdr_method': 'fdr_bh'
        }
        
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved analysis summary to {args.output}")

if __name__ == '__main__':
    main()