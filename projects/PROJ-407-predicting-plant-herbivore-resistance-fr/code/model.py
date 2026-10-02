import os
import json
import logging
import pickle
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
from scipy import stats

# Import config for constants
try:
    from config import RANDOM_SEED, DATA_ROOT
except ImportError:
    # Fallback if run as script without package structure
    RANDOM_SEED = 42
    DATA_ROOT = 'data'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """Load the processed dataset (PCA reduced or harmonized)."""
    logger.info(f"Loading processed data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    return pd.read_csv(input_path)

def train_random_forest(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    logger.info("Training Random Forest Regressor...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    model.fit(X, y)
    logger.info("Model training complete.")
    return model

def evaluate_model(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
    """Calculate R² and MSE."""
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    logger.info(f"Evaluation - R²: {r2:.4f}, MSE: {mse:.4f}")
    return {"r2_score": r2, "mse": mse}

def extract_feature_importance(model: RandomForestRegressor, feature_names: List[str]) -> pd.DataFrame:
    """Extract feature importance from the trained model."""
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "metabolite_name": feature_names,
        "importance_score": importances
    })
    return importance_df

def extract_feature_importance_with_data(
    model: RandomForestRegressor,
    X_train: pd.DataFrame,
    y_train: pd.Series
) -> pd.DataFrame:
    """
    Extract feature importance along with unadjusted p-values and correlation coefficients.
    
    Returns a DataFrame with columns:
    - metabolite_name
    - importance_score (from RF)
    - unadjusted_p_value (from correlation test)
    - correlation_coefficient (from correlation test)
    """
    # 1. Extract RF importance
    feature_names = X_train.columns.tolist()
    importances = model.feature_importances_
    
    # 2. Calculate correlations and p-values on the training set
    # Note: T032 specifies correlations on test set, but T024 asks for 
    # feature importance table. Usually, feature importance is paired 
    # with the data used to derive it. However, to avoid leakage if this 
    # is used for biomarker selection, we should be careful. 
    # The task description for T024 says "rank top metabolites".
    # T032 explicitly says "on the test set". 
    # Since T024 depends on T022 (training) and T021 (split), and T032 
    # also depends on T021, T029a. 
    # The prompt for T024 says "Output: Save feature importance table...".
    # It does not explicitly say "use test set" for the correlation column, 
    # but T032 says "univariate correlation calculation ... on the test set".
    # To be safe and consistent with T032's leakage prevention, we will 
    # calculate correlations on the provided X_train/y_train here if 
    # the caller passes them, OR we assume the caller passes the 
    # appropriate split. 
    # Given the function signature takes X_train/y_train, we calculate 
    # correlations on these. If the caller passes the test set, it will 
    # be test correlations. The task T024 is part of US2 (Modeling), 
    # while T032 is US3 (Validation). 
    # Let's calculate correlations on the data passed to this function.
    
    correlations = []
    p_values = []
    
    for metabolite in feature_names:
        col_data = X_train[metabolite]
        # Handle constant columns or NaNs
        if col_data.nunique() < 2:
            correlations.append(0.0)
            p_values.append(1.0)
            continue
        
        # Use Pearson for continuous, Spearman for ordinal (resistance)
        # Assuming y_train is numeric (continuous or ordinal 1,2,3)
        # We'll use Spearman as it's more robust for ordinal resistance scores
        corr, p_val = stats.spearmanr(col_data, y_train)
        correlations.append(corr)
        p_values.append(p_val)
    
    df = pd.DataFrame({
        "metabolite_name": feature_names,
        "importance_score": importances,
        "unadjusted_p_value": p_values,
        "correlation_coefficient": correlations
    })
    
    # Sort by importance score descending
    df = df.sort_values(by="importance_score", ascending=False).reset_index(drop=True)
    return df

def save_model(model: RandomForestRegressor, output_path: str) -> None:
    """Save the trained model to a pickle file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

def save_metrics(metrics: Dict[str, float], output_path: str) -> None:
    """Save evaluation metrics to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def save_feature_importance(df: pd.DataFrame, output_path: str) -> None:
    """Save feature importance DataFrame to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train and evaluate Random Forest model")
    parser.add_argument("--input", type=str, required=True, help="Path to processed data CSV")
    parser.add_argument("--output", type=str, required=True, help="Output directory for artifacts")
    parser.add_argument("--model-output", type=str, default=None, help="Path to save model (optional)")
    parser.add_argument("--metrics-output", type=str, default=None, help="Path to save metrics (optional)")
    parser.add_argument("--importance-output", type=str, default=None, help="Path to save feature importance (optional)")
    args = parser.parse_args()

    # Determine input file based on existence (fallback logic from T022)
    input_path = args.input
    if not os.path.exists(input_path):
        # Check fallbacks
        if os.path.exists("data/interim/batch_corrected_data.csv"):
            input_path = "data/interim/batch_corrected_data.csv"
        elif os.path.exists("data/processed/pca_reduced.csv"):
            input_path = "data/processed/pca_reduced.csv"
        elif os.path.exists("data/interim/harmonized.csv"):
            input_path = "data/interim/harmonized.csv"
        else:
            raise FileNotFoundError(f"No valid input data found. Searched: {input_path}, fallbacks missing.")
    
    logger.info(f"Using input data: {input_path}")
    data = load_processed_data(input_path)

    # Identify target and features
    # Assuming 'resistance' or 'resistance_ordinal' is the target
    target_col = 'resistance_ordinal' if 'resistance_ordinal' in data.columns else 'resistance'
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    X = data.drop(columns=[target_col])
    y = data[target_col]

    # Ensure all features are numeric
    X = X.select_dtypes(include=[np.number])

    if X.shape[1] == 0:
        raise ValueError("No numeric features found for training.")

    # Train model
    model = train_random_forest(X, y)

    # Evaluate
    metrics = evaluate_model(model, X, y)

    # Extract feature importance with data
    importance_df = extract_feature_importance_with_data(model, X, y)

    # Determine output paths
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = args.model_output or os.path.join(output_dir, "model.pkl")
    metrics_path = args.metrics_output or os.path.join(output_dir, "model_metrics.json")
    importance_path = args.importance_output or os.path.join(output_dir, "feature_importance.csv")

    # Save artifacts
    save_model(model, model_path)
    save_metrics(metrics, metrics_path)
    save_feature_importance(importance_df, importance_path)

    logger.info("All artifacts saved successfully.")

if __name__ == "__main__":
    main()