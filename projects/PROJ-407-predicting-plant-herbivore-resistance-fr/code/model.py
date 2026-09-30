import os
import json
import logging
import pickle
import argparse
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, accuracy_score
from scipy import stats

from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load processed data and separate features (metabolites) from target (resistance).
    
    Args:
        input_path: Path to the processed CSV file.
        
    Returns:
        Tuple of (features_df, target_series)
    """
    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Identify target column
    if 'resistance' not in df.columns:
        raise ValueError("Input file must contain a 'resistance' column")
    
    # Identify metabolite columns (assume they start with 'metabolite_' or are all numeric except resistance)
    # Based on typical data model, we look for columns that are not 'sample_id', 'genotype_id', 'resistance'
    exclude_cols = ['sample_id', 'genotype_id', 'resistance']
    metabolite_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in [np.float64, np.float32, np.int64, np.int32]]
    
    if not metabolite_cols:
        raise ValueError("No metabolite columns found in input data")
    
    logger.info(f"Found {len(metabolite_cols)} metabolite features")
    
    X = df[metabolite_cols]
    y = df['resistance']
    
    return X, y, metabolite_cols

def train_random_forest(X: pd.DataFrame, y: pd.Series, random_seed: int = 42) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Trained RandomForestRegressor model.
    """
    logger.info("Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=random_seed,
        n_jobs=-1
    )
    model.fit(X, y)
    logger.info("Model training complete.")
    return model

def evaluate_model(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
    """
    Evaluate model performance.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        y: True target values.
        
    Returns:
        Dictionary of metrics (R2, MSE).
    """
    logger.info("Evaluating model...")
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    
    # If y is integer-like, we can also compute accuracy for classification-like view
    # But strictly for regression, we stick to R2 and MSE.
    # If the task implies classification accuracy, we would need to discretize y.
    # For now, we return R2 and MSE.
    
    metrics = {
        'r2': float(r2),
        'mse': float(mse)
    }
    
    logger.info(f"Model evaluation complete. R2: {r2:.4f}, MSE: {mse:.4f}")
    return metrics

def extract_feature_importance(model: RandomForestRegressor, feature_names: list) -> pd.DataFrame:
    """
    Extract feature importance from the trained model.
    
    Args:
        model: Trained RandomForestRegressor.
        feature_names: List of feature names.
        
    Returns:
        DataFrame with feature names and importance scores.
    """
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        'metabolite_name': feature_names,
        'importance_score': importances
    })
    return importance_df.sort_values(by='importance_score', ascending=False)

def extract_feature_importance_with_data(
    model: RandomForestRegressor, 
    X: pd.DataFrame, 
    y: pd.Series,
    feature_names: list
) -> pd.DataFrame:
    """
    Extract feature importance and calculate correlation coefficients and p-values.
    
    Args:
        model: Trained RandomForestRegressor.
        X: Feature matrix.
        y: Target vector.
        feature_names: List of feature names.
        
    Returns:
        DataFrame with metabolite_name, importance_score, unadjusted_p_value, correlation_coefficient.
    """
    # 1. Get Feature Importance from Random Forest
    importance_df = extract_feature_importance(model, feature_names)
    
    # 2. Calculate Correlations (Pearson) for each metabolite vs resistance
    correlations = []
    p_values = []
    
    for col in feature_names:
        corr, p_val = stats.pearsonr(X[col], y)
        correlations.append(corr)
        p_values.append(p_val)
    
    # Add to DataFrame
    importance_df['correlation_coefficient'] = correlations
    importance_df['unadjusted_p_value'] = p_values
    
    return importance_df

def save_model(model: RandomForestRegressor, output_path: str) -> None:
    """
    Save the trained model to a pickle file.
    
    Args:
        model: Trained model.
        output_path: Path to save the model.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

def save_metrics(metrics: Dict[str, float], output_path: str) -> None:
    """
    Save evaluation metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics.
        output_path: Path to save the metrics.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def save_feature_importance(df: pd.DataFrame, output_path: str) -> None:
    """
    Save feature importance table to a CSV file.
    
    Args:
        df: DataFrame with feature importance data.
        output_path: Path to save the CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train and evaluate Random Forest model for herbivore resistance prediction.")
    parser.add_argument('--input', type=str, required=True, help='Path to processed CSV file.')
    parser.add_argument('--output', type=str, required=True, help='Directory to save model, metrics, and feature importance.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed.')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    ensure_directories(args.output)
    
    # Load data
    X, y, feature_names = load_processed_data(args.input)
    
    # Train model
    model = train_random_forest(X, y, args.seed)
    
    # Evaluate model
    metrics = evaluate_model(model, X, y)
    
    # Extract feature importance with correlations
    feature_importance_df = extract_feature_importance_with_data(model, X, y, feature_names)
    
    # Define output paths
    model_path = os.path.join(args.output, 'model.pkl')
    metrics_path = os.path.join(args.output, 'model_metrics.json')
    importance_path = os.path.join(args.output, 'feature_importance.csv')
    
    # Save artifacts
    save_model(model, model_path)
    save_metrics(metrics, metrics_path)
    save_feature_importance(feature_importance_df, importance_path)
    
    logger.info("Pipeline completed successfully.")

if __name__ == '__main__':
    main()
