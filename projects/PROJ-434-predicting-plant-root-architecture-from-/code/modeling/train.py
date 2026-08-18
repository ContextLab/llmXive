import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold, LeaveOneGroupOut
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_squared_error
from scipy.stats import ttest_rel

# Local imports based on API surface
from utils.stats import (
    calculate_metrics,
    calculate_baseline_r2,
    delta_r2,
    permutation_test,
    stratified_permutation_test
)
from utils.exceptions import DataQualityError
from utils.config import Config, load_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def preprocess_data(df: pd.DataFrame, target_cols: List[str], species_col: str = 'Species') -> Tuple[pd.DataFrame, LabelEncoder]:
    """
    Preprocess data for modeling: encode species, handle missing values,
    and separate features/targets.
    """
    logger.info("Preprocessing data...")
    
    # Encode Species
    le = LabelEncoder()
    df = df.copy()
    df['Species_encoded'] = le.fit_transform(df[species_col].astype(str))
    
    # Define features (Soil + Encoded Species)
    feature_cols = [c for c in df.columns if c not in target_cols + [species_col]]
    
    X = df[feature_cols].copy()
    y = df[target_cols].copy()
    
    # Drop rows with any NaN in features or targets
    mask = ~(X.isna().any(axis=1) | y.isna().any(axis=1))
    X = X[mask]
    y = y[mask]
    
    logger.info(f"Preprocessed data shape: {X.shape}")
    return X, y, le

def train_model(X: pd.DataFrame, y: pd.DataFrame, random_state: int = 42) -> Dict[str, Any]:
    """
    Train a Random Forest model for each target variable.
    """
    models = {}
    logger.info("Training models...")
    for col in y.columns:
        model = RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)
        model.fit(X, y[col])
        models[col] = model
        logger.info(f"Trained model for {col}")
    return models

def run_stratified_cv(X: pd.DataFrame, y: pd.DataFrame, species: pd.Series, n_splits: int = 5) -> Dict[str, Any]:
    """
    Run Stratified 5-Fold Cross-Validation based on Species.
    """
    logger.info("Running Stratified 5-Fold CV...")
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    results = {col: {'r2': [], 'rmse': []} for col in y.columns}
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(X, species)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        models = train_model(X_train, y_train)
        
        for col in y.columns:
            y_pred = models[col].predict(X_test)
            r2 = r2_score(y_test[col], y_pred)
            rmse = np.sqrt(mean_squared_error(y_test[col], y_pred))
            results[col]['r2'].append(r2)
            results[col]['rmse'].append(rmse)
            logger.debug(f"Fold {fold+1} - {col}: R²={r2:.4f}, RMSE={rmse:.4f}")
    
    mean_results = {}
    for col in y.columns:
        mean_results[col] = {
            'mean_r2': float(np.mean(results[col]['r2'])),
            'mean_rmse': float(np.mean(results[col]['rmse'])),
            'std_r2': float(np.std(results[col]['r2'])),
            'std_rmse': float(np.std(results[col]['rmse']))
        }
    
    return mean_results

def run_loso_cv(X: pd.DataFrame, y: pd.DataFrame, species: pd.Series) -> Dict[str, Any]:
    """
    Run Leave-One-Species-Out Cross-Validation.
    """
    logger.info("Running LOSO CV...")
    logo = LeaveOneGroupOut()
    
    results = {col: {'r2': []} for col in y.columns}
    
    for train_idx, test_idx in logo.split(X, y, groups=species):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        models = train_model(X_train, y_train)
        
        for col in y.columns:
            y_pred = models[col].predict(X_test)
            r2 = r2_score(y_test[col], y_pred)
            results[col]['r2'].append(r2)
            logger.debug(f"LOSO - {col}: R²={r2:.4f}")
    
    return {col: {'mean_r2': float(np.mean(v['r2'])), 'std_r2': float(np.std(v['r2']))} for col, v in results.items()}

def run_spatial_cv(X: pd.DataFrame, y: pd.DataFrame, lat: pd.Series, lon: pd.Series, n_splits: int = 5) -> Dict[str, Any]:
    """
    Run Spatial Cross-Validation by clustering coordinates.
    """
    logger.info("Running Spatial CV...")
    # Simple spatial binning for demonstration of spatial split
    # In a real scenario, use k-means or grid-based clustering
    lat_bins = pd.qcut(lat, q=n_splits, duplicates='drop')
    lon_bins = pd.qcut(lon, q=n_splits, duplicates='drop')
    spatial_group = lat_bins.astype(str) + "_" + lon_bins.astype(str)
    
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    results = {col: {'r2': []} for col in y.columns}
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(X, spatial_group)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        models = train_model(X_train, y_train)
        
        for col in y.columns:
            y_pred = models[col].predict(X_test)
            r2 = r2_score(y_test[col], y_pred)
            results[col]['r2'].append(r2)
            logger.debug(f"Spatial Fold {fold+1} - {col}: R²={r2:.4f}")
    
    return {col: {'mean_r2': float(np.mean(v['r2'])), 'std_r2': float(np.std(v['r2']))} for col, v in results.items()}

def run_nested_permutation_tests(X: pd.DataFrame, y: pd.DataFrame, models: Dict[str, Any], n_iterations: int = 1000, species: Optional[pd.Series] = None) -> Dict[str, Any]:
    """
    Run nested permutation tests to assess feature importance significance.
    """
    logger.info(f"Running nested permutation tests ({n_iterations} iterations)...")
    results = {}
    
    for col in y.columns:
        y_true = y[col].values
        y_pred_base = models[col].predict(X).values
        obs_r2 = r2_score(y_true, y_pred_base)
        
        # Baseline R2 (mean prediction)
        baseline_r2_val = calculate_baseline_r2(y_true, y_pred_base)
        
        # Permutation test
        if species is not None:
            # Stratified permutation for Model B
            p_val = stratified_permutation_test(X, y_true, models[col], n_iterations=n_iterations, groups=species)
        else:
            p_val = permutation_test(X, y_true, models[col], n_iterations=n_iterations)
        
        results[col] = {
            'obs_r2': float(obs_r2),
            'baseline_r2': float(baseline_r2_val),
            'delta_r2': float(obs_r2 - baseline_r2_val),
            'p_value': float(p_val)
        }
        logger.info(f"Permutation test for {col}: R²={obs_r2:.4f}, ΔR²={obs_r2 - baseline_r2_val:.4f}, p={p_val:.4f}")
    
    return results

def enforce_sc002(permutation_results: Dict[str, Any], delta_threshold: float = 0.05, p_threshold: float = 0.05) -> Dict[str, Any]:
    """
    Enforce Success Criterion 002 (SC-002):
    ΔR² ≥ 0.05 AND p < 0.05.
    Reports pass/fail status for each target variable.
    """
    logger.info("Enforcing SC-002...")
    report = {}
    all_passed = True
    
    for col, metrics in permutation_results.items():
        delta_r2_val = metrics['delta_r2']
        p_val = metrics['p_value']
        
        passed = (delta_r2_val >= delta_threshold) and (p_val < p_threshold)
        status = "PASS" if passed else "FAIL"
        
        if not passed:
            all_passed = False
        
        report[col] = {
            'delta_r2': delta_r2_val,
            'p_value': p_val,
            'status': status,
            'criteria': f"ΔR² >= {delta_threshold} AND p < {p_threshold}"
        }
        logger.info(f"SC-002 for {col}: {status} (ΔR²={delta_r2_val:.4f}, p={p_val:.4f})")
    
    report['overall_status'] = "PASS" if all_passed else "FAIL"
    return report

def generate_feature_importance_plot(models: Dict[str, Any], feature_names: List[str], output_path: str):
    """
    Generate feature importance bar chart.
    """
    logger.info(f"Generating feature importance plot: {output_path}")
    plt.figure(figsize=(10, 6))
    
    # Assume single model for simplicity or iterate if multiple
    # Here we plot the first model's importance as an example
    first_model_name = next(iter(models))
    importances = models[first_model_name].feature_importances_
    
    sns.barplot(x=importances, y=feature_names)
    plt.title(f"Feature Importance ({first_model_name})")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def main():
    """
    Main execution flow for training and validation, including SC-002 enforcement.
    """
    logger.info("Starting training pipeline...")
    
    # Load configuration
    config = load_environment()
    data_path = Path(config.get('DATA_PATH', 'data/processed/merged_dataset.csv'))
    output_dir = Path(config.get('OUTPUT_DIR', 'artifacts'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Define targets
    target_cols = ['RootDepth', 'RootBiomass'] # Adjust based on actual schema
    species_col = 'Species'
    lat_col = 'Latitude'
    lon_col = 'Longitude'
    
    # Preprocess
    X, y, le = preprocess_data(df, target_cols, species_col)
    species_encoded = df.loc[X.index, species_col]
    lat = df.loc[X.index, lat_col]
    lon = df.loc[X.index, lon_col]
    
    # Run Stratified CV
    strat_results = run_stratified_cv(X, y, species_encoded)
    
    # Run LOSO
    loso_results = run_loso_cv(X, y, species_encoded)
    
    # Run Spatial CV
    spatial_results = run_spatial_cv(X, y, lat, lon)
    
    # Train final models for permutation tests (using full data)
    final_models = train_model(X, y)
    
    # Run Permutation Tests
    perm_results = run_nested_permutation_tests(X, y, final_models, n_iterations=1000, species=species_encoded)
    
    # Enforce SC-002
    sc002_report = enforce_sc002(perm_results)
    
    # Save results
    metrics_output = {
        'stratified_cv': strat_results,
        'loso_cv': loso_results,
        'spatial_cv': spatial_results,
        'permutation_tests': perm_results,
        'sc002_report': sc002_report
    }
    
    with open(output_dir / 'model_metrics.json', 'w') as f:
        json.dump(metrics_output, f, indent=2)
    
    # Generate Feature Importance Plot
    feature_names = [c for c in df.columns if c not in target_cols + [species_col, lat_col, lon_col]]
    generate_feature_importance_plot(final_models, feature_names, str(output_dir / 'feature_importance.png'))
    
    logger.info("Pipeline completed successfully.")
    print(f"SC-002 Status: {sc002_report['overall_status']}")
    return sc002_report['overall_status']

if __name__ == '__main__':
    main()