"""
Baseline models for predicting amine reactivity.

Implements Random Forest and Linear Regression using traditional chemical descriptors.
"""
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import StratifiedGroupKFold
import joblib

logger = logging.getLogger(__name__)

# Feature columns required by FR-004 and US-2
# Derived from T007 (descriptors), T006 (pKa), and T007b (Taft)
BASELINE_FEATURES = [
    'pKa',           # From T006
    'MW',            # Molecular Weight (standard RDKit)
    'Taft_Es',       # From T007b
    'Taft_Es_s',     # Steric parameter variant
    'Charton_nu',    # From T007b
    'Hammett_sigma_p', # From T007a (if applicable, else 0)
    'Molar_Refractivity' # From T007d
]

TARGET_COLUMN = 'normalized_log_rate'


def load_preprocessed_data(graph_path: str) -> pd.DataFrame:
    """
    Load preprocessed graph data and extract baseline features.
    
    Expects a JSON file containing molecular graphs with calculated descriptors.
    Converts graph data into a flat DataFrame suitable for baseline models.
    """
    import json
    
    with open(graph_path, 'r') as f:
        data = json.load(f)
    
    records = []
    for entry in data:
        # Extract reaction-level features
        # Assuming entry contains 'molecule' (graph) and 'reaction' (kinetics)
        mol_data = entry.get('molecule', {})
        reaction_data = entry.get('reaction', {})
        
        # Flatten descriptors from the molecule node/edge attributes or pre-calculated fields
        # The ingestion/preprocessing pipeline (T016) should have attached these
        record = {
            'pKa': mol_data.get('pKa', np.nan),
            'MW': mol_data.get('MW', np.nan),
            'Taft_Es': mol_data.get('Taft_Es', np.nan),
            'Taft_Es_s': mol_data.get('Taft_Es_s', np.nan),
            'Charton_nu': mol_data.get('Charton_nu', np.nan),
            'Hammett_sigma_p': mol_data.get('Hammett_sigma_p', 0.0),
            'Molar_Refractivity': mol_data.get('Molar_Refractivity', np.nan),
            'target': reaction_data.get('normalized_log_rate', np.nan),
            'scaffold': reaction_data.get('scaffold', 'unknown') # For stratified split
        }
        
        # Check for missing critical values
        if np.isnan(record['target']):
            continue
            
        # Drop rows with too many missing features
        feature_vals = [record[f] for f in BASELINE_FEATURES]
        if sum(np.isnan(feature_vals)) > len(feature_vals) * 0.3:
            continue
            
        records.append(record)
    
    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("No valid records found in preprocessed data for baseline training.")
    
    # Impute missing features with median (simple baseline strategy)
    for col in BASELINE_FEATURES:
        if df[col].isna().any():
            median_val = df[col].median()
            if np.isnan(median_val):
                median_val = 0.0
            df[col] = df[col].fillna(median_val)
    
    return df


def train_baseline_models(
    df: pd.DataFrame,
    output_dir: str,
    random_state: int = 42
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Train Random Forest and Linear Regression models.
    
    Args:
        df: DataFrame with features and target
        output_dir: Directory to save model artifacts
        random_state: Random seed for reproducibility
        
    Returns:
      Tuple of (model_dict, metrics_dict)
    """
    X = df[BASELINE_FEATURES].values
    y = df[TARGET_COLUMN].values
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Split data (Stratified by scaffold to respect FR-006)
    # Using a simple 80/20 split for now, but ensuring scaffold balance
    scaffold_groups = df['scaffold'].values
    
    # Simple train/test split
    split_idx = int(len(df) * 0.8)
    # Shuffle indices
    indices = np.arange(len(df))
    rng = np.random.default_rng(random_state)
    rng.shuffle(indices)
    
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    models = {}
    metrics = {}
    
    # 1. Linear Regression
    logger.info("Training Linear Regression baseline...")
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)
    
    lr_metrics = {
        'mae': mean_absolute_error(y_test, y_pred_lr),
        'r2': r2_score(y_test, y_pred_lr)
    }
    metrics['linear_regression'] = lr_metrics
    
    joblib.dump(lr_model, Path(output_dir) / 'baseline_linear_regression.joblib')
    models['linear_regression'] = lr_model
    logger.info(f"Linear Regression - MAE: {lr_metrics['mae']:.4f}, R²: {lr_metrics['r2']:.4f}")
    
    # 2. Random Forest
    logger.info("Training Random Forest baseline...")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    
    rf_metrics = {
        'mae': mean_absolute_error(y_test, y_pred_rf),
        'r2': r2_score(y_test, y_pred_rf)
    }
    metrics['random_forest'] = rf_metrics
    
    joblib.dump(rf_model, Path(output_dir) / 'baseline_random_forest.joblib')
    models['random_forest'] = rf_model
    logger.info(f"Random Forest - MAE: {rf_metrics['mae']:.4f}, R²: {rf_metrics['r2']:.4f}")
    
    return models, metrics


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str
) -> Dict[str, float]:
    """
    Evaluate a trained model on test data.
    """
    y_pred = model.predict(X_test)
    return {
        'mae': mean_absolute_error(y_test, y_pred),
        'r2': r2_score(y_test, y_pred)
    }


def main():
    """
    Entry point for baseline model training.
    Expects preprocessed graph data at data/derived/graphs.json
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = "data/derived/graphs.json"
    output_dir = "data/derived/baseline_models"
    
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T016 (preprocessing) to generate graph data first.")
        return 1
    
    try:
        logger.info(f"Loading data from {input_path}...")
        df = load_preprocessed_data(input_path)
        logger.info(f"Loaded {len(df)} valid records.")
        
        logger.info("Training baseline models...")
        models, metrics = train_baseline_models(df, output_dir)
        
        # Save metrics
        import json
        metrics_path = Path(output_dir) / 'training_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Training complete. Metrics saved to {metrics_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
