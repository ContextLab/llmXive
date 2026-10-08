import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from code.logging_config import setup_logging
from code.config import SEED, DATA_PATH

logger = setup_logging(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the processed descriptors and target data.
    Expects data/processed/descriptors.csv to exist.
    """
    path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed descriptors not found at {path}. "
                                "Run the descriptor pipeline first.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Separate features and target.
    Assumes the target column is 'log_conductivity' or similar, or the last column if not specified.
    For this task, we assume the target is explicitly named 'log_conductivity' or 'log_HOMO_LUMO_gap'.
    If not, we look for a column matching 'log_' or the config TARGET_VAR.
    """
    from code.config import TARGET_VAR
    
    target_col = None
    # Check for standard log-transformed targets
    possible_targets = [f'log_{TARGET_VAR}', TARGET_VAR, 'log_conductivity', 'log_HOMO_LUMO_gap']
    
    for t in possible_targets:
        if t in df.columns:
            target_col = t
            break
    
    if target_col is None:
        # Fallback: assume the last column is the target if it looks numeric
        # This is a heuristic for robustness
        logger.warning(f"Could not find standard target column. Checking last column.")
        if pd.api.types.is_numeric_dtype(df.iloc[:, -1]):
            target_col = df.columns[-1]
            logger.info(f"Using '{target_col}' as target by heuristic.")
        else:
            raise ValueError("Could not identify target column in the dataset.")

    # Features are all columns except the target
    feature_cols = [c for c in df.columns if c != target_col]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle NaNs if any (though T019 should have removed them)
    if np.isnan(X).any() or np.isnan(y).any():
        logger.warning("NaN values detected in features or target. Dropping rows.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        feature_cols = [c for c in feature_cols] # Keep order

    return X, y, feature_cols

def train_model(X: np.ndarray, y: np.ndarray) -> RandomForestRegressor:
    """
    Train a Random Forest model on the provided data.
    Uses the same hyperparameters as T029 for consistency.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=SEED,
        n_jobs=-1
    )
    model.fit(X, y)
    logger.info("Model trained successfully.")
    return model

def compute_feature_importance(model, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
    """
    Compute permutation importance.
    """
    result = permutation_importance(
        model, X, y, 
        n_repeats=10, 
        random_state=SEED, 
        n_jobs=-1
    )
    
    # Create a DataFrame with feature names and their importance scores
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance_score': result.importances_mean
    })
    
    # Sort by importance score descending
    importance_df = importance_df.sort_values(by='importance_score', ascending=False).reset_index(drop=True)
    
    return importance_df

def save_feature_importance_csv(importance_df: pd.DataFrame, output_path: str) -> None:
    """
    Save the ranked feature importance to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")
    
    # Verification
    if os.path.exists(output_path):
        logger.info(f"Verification: File exists at {output_path}")
        loaded = pd.read_csv(output_path)
        assert 'feature' in loaded.columns and 'importance_score' in loaded.columns
        logger.info(f"Verification: Columns correct. Rows: {len(loaded)}")
    else:
        raise RuntimeError(f"Failed to create file at {output_path}")

def run_feature_importance_analysis() -> pd.DataFrame:
    """
    Main orchestration function for T040.
    1. Load data.
    2. Prepare features/target.
    3. Train model (on the final VIF-filtered data which is assumed to be in descriptors.csv).
    4. Compute permutation importance.
    5. Save to data/processed/feature_importance.csv.
    """
    logger.info("Starting Feature Importance Analysis (T040)")
    
    # 1. Load data
    df = load_processed_data()
    
    # 2. Prepare features
    X, y, feature_names = prepare_features_and_target(df)
    logger.info(f"Prepared {X.shape[0]} samples with {X.shape[1]} features.")
    
    # 3. Train model
    model = train_model(X, y)
    
    # 4. Compute importance
    importance_df = compute_feature_importance(model, X, y, feature_names)
    
    # 5. Save
    output_path = os.path.join(DATA_PATH, 'processed', 'feature_importance.csv')
    save_feature_importance_csv(importance_df, output_path)
    
    logger.info("Feature Importance Analysis completed successfully.")
    return importance_df

def main():
    """
    CLI entry point.
    """
    parser = argparse.ArgumentParser(description="Compute and save feature importance rankings.")
    args = parser.parse_args()
    
    try:
        run_feature_importance_analysis()
    except Exception as e:
        logger.error(f"Feature importance analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()