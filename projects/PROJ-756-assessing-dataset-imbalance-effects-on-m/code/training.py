"""
Training module for materials property prediction models.
Handles both baseline (skewed) and balanced dataset training for Random Forest and Gradient Boosting.
"""

import os
import sys
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/training.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = PROJECT_ROOT / "data" / "models"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_data(file_path: Path) -> pd.DataFrame:
    """
    Load processed data from a CSV or Parquet file.
    
    Args:
        file_path: Path to the data file.
        
    Returns:
        Loaded DataFrame.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    if file_path.suffix == '.csv':
        return pd.read_csv(file_path)
    elif file_path.suffix == '.parquet':
        return pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def identify_targets_and_features(df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Identify target and feature columns from the DataFrame.
    
    Args:
        df: Input DataFrame.
        target_column: Name of the target column.
        
    Returns:
        Tuple of (features_df, target_series, feature_names_list).
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data. Available columns: {df.columns.tolist()}")
    
    # Assume all columns except target are features
    feature_columns = [col for col in df.columns if col != target_column]
    
    # Filter out any non-numeric columns if necessary
    numeric_features = df[feature_columns].select_dtypes(include=[np.number]).columns
    features_df = df[numeric_features]
    target_series = df[target_column]
    
    logger.info(f"Identified {len(features_df.columns)} features and target '{target_column}'")
    return features_df, target_series, list(features_df.columns)


def train_models(
    X: pd.DataFrame,
    y: pd.Series,
    model_type: str = 'all',
    test_size: float = 0.2,
    random_state: int = 42,
    balanced: bool = False,
    property_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Train Random Forest and/or Gradient Boosting models.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        model_type: 'rf', 'gb', or 'all'.
        test_size: Proportion of data for testing.
        random_state: Random seed for reproducibility.
        balanced: Boolean flag indicating if this is balanced data training (US2).
        property_name: Name of the property being modeled for logging.
        
    Returns:
        Dictionary containing models, metrics, and metadata.
    """
    logger.info(f"Training {'balanced' if balanced else 'skewed'} models for property: {property_name}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Scale features (optional but good practice for some algorithms, though trees don't strictly need it)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Convert back to DataFrame to preserve column names if needed by SHAP later
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X.columns, index=X_train.index)
    X_test_scaled_df = pd.DataFrame(X_test_scaled, columns=X.columns, index=X_test.index)
    
    models = {}
    metrics = {}
    
    config = {
        'random_state': random_state,
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'learning_rate': 0.1,
        'subsample': 0.8
    }
    
    models_to_train = []
    if model_type in ['rf', 'all']:
        models_to_train.append('rf')
    if model_type in ['gb', 'all']:
        models_to_train.append('gb')
        
    for m_type in models_to_train:
        logger.info(f"Training {m_type} model...")
        
        if m_type == 'rf':
            model = RandomForestRegressor(
                n_estimators=config['n_estimators'],
                max_depth=config['max_depth'],
                min_samples_split=config['min_samples_split'],
                min_samples_leaf=config['min_samples_leaf'],
                random_state=config['random_state'],
                n_jobs=-1
            )
        elif m_type == 'gb':
            model = GradientBoostingRegressor(
                n_estimators=config['n_estimators'],
                max_depth=config['max_depth'],
                learning_rate=config['learning_rate'],
                subsample=config['subsample'],
                random_state=config['random_state']
            )
        
        # Train
        model.fit(X_train_scaled_df, y_train)
        
        # Predict
        y_pred = model.predict(X_test_scaled_df)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        models[m_type] = {
            'model': model,
            'scaler': scaler,
            'metrics': {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'test_size': len(y_test),
                'train_size': len(y_train)
            }
        }
        
        logger.info(f"{m_type.upper()} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
    
    result = {
        'models': models,
        'property': property_name,
        'balanced': balanced,
        'config': config,
        'split_info': {
            'train_size': len(y_train),
            'test_size': len(y_test),
            'random_state': random_state
        }
    }
    
    return result


def save_results(results: Dict[str, Any], property_name: str, balanced: bool = False) -> Path:
    """
    Save trained models and metadata to disk.
    
    Args:
        results: Dictionary containing models and metrics.
        property_name: Name of the property.
        balanced: Boolean flag indicating if this is balanced data training.
        
    Returns:
        Path to the saved file.
    """
    filename = f"models_{property_name}_{'balanced' if balanced else 'skewed'}.pkl"
    file_path = MODELS_DIR / filename
    
    with open(file_path, 'wb') as f:
        pickle.dump(results, f)
        
    logger.info(f"Saved models to {file_path}")
    return file_path


def main():
    """
    Main entry point for training pipeline.
    Supports two modes:
    1. Baseline (Skewed): Loads processed data, trains on original distribution.
    2. Balanced: Loads resampled data, trains on balanced distribution (US2).
    
    Usage:
        python code/training.py --property <property_name> --balanced [True|False]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Train materials property prediction models.")
    parser.add_argument('--property', type=str, required=True, help="Name of the property to model")
    parser.add_argument('--balanced', type=str, default='False', help="Whether to train on balanced data (True/False)")
    parser.add_argument('--input_file', type=str, default=None, help="Optional specific input file path")
    parser.add_argument('--target', type=str, default=None, help="Optional target column name")
    
    args = parser.parse_args()
    
    balanced = args.balanced.lower() == 'true'
    property_name = args.property
    
    # Determine input file
    if args.input_file:
        input_path = Path(args.input_file)
    else:
        # Default naming convention based on balanced flag
        prefix = "balanced" if balanced else "skewed"
        input_path = PROCESSED_DATA_DIR / f"{property_name}_{prefix}_descriptors.csv"
        
    if not input_path.exists():
        # Fallback to generic processed file if specific one doesn't exist
        input_path = PROCESSED_DATA_DIR / f"{property_name}_descriptors.csv"
        if not input_path.exists():
            logger.error(f"No input data found for property {property_name}. Checked: {input_path}")
            sys.exit(1)
    
    # Determine target
    target_col = args.target
    if not target_col:
        # Default target naming convention
        target_col = property_name
    
    try:
        # Load data
        df = load_data(input_path)
        
        # Identify features and target
        X, y, feature_names = identify_targets_and_features(df, target_col)
        
        if len(X) < 10:
            logger.error(f"Insufficient data for property {property_name}: {len(X)} samples.")
            sys.exit(1)
        
        # Train models
        results = train_models(
            X, y, 
            model_type='all', 
            balanced=balanced,
            property_name=property_name
        )
        
        # Save results
        save_path = save_results(results, property_name, balanced)
        
        # Print summary
        print(f"\n--- Training Summary for {property_name} ({'Balanced' if balanced else 'Skewed'}) ---")
        for model_type, data in results['models'].items():
            m = data['metrics']
            print(f"{model_type.upper()}: MAE={m['mae']:.4f}, RMSE={m['rmse']:.4f}, R²={m['r2']:.4f}")
        print(f"Saved to: {save_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()