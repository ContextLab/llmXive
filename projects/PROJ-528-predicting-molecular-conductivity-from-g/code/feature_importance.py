import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from code.config import SEED

logger = logging.getLogger(__name__)

def load_processed_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data not found: {path}")
    return pd.read_csv(path)

def prepare_features_and_target(df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, pd.Series]:
    feature_cols = [c for c in df.columns if c not in ['smiles', target_col, 'valid', 'error_msg']]
    X = df[feature_cols].values
    y = df[target_col]
    return X, y

def train_model(X: np.ndarray, y: pd.Series, seed: int) -> RandomForestRegressor:
    model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed)
    model.fit(X, y)
    return model

def compute_feature_importance(model: RandomForestRegressor, X: np.ndarray, y: pd.Series, seed: int) -> pd.DataFrame:
    result = permutation_importance(model, X, y, n_repeats=10, random_state=seed)
    importance_scores = result.importances_mean
    # Assuming columns are in order of X
    # We need feature names. Let's assume they are passed or we read from df.
    # For this function, we return a list of scores, caller maps to names.
    return pd.DataFrame({'importance_score': importance_scores})

def save_feature_importance_csv(importance_df: pd.DataFrame, feature_names: List[str], output_path: str) -> None:
    importance_df['feature'] = feature_names
    importance_df = importance_df.sort_values('importance_score', ascending=False)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")

def run_feature_importance_analysis(
    data_path: str,
    target_col: str,
    output_path: str,
    seed: int = SEED
) -> None:
    df = load_processed_data(data_path)
    X, y = prepare_features_and_target(df, target_col)
    model = train_model(X, y, seed)
    importance_df = compute_feature_importance(model, X, y, seed)
    feature_names = [c for c in df.columns if c not in ['smiles', target_col, 'valid', 'error_msg']]
    save_feature_importance_csv(importance_df, feature_names, output_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run feature importance analysis (T040)")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv")
    parser.add_argument("--target", type=str, default="conductivity")
    parser.add_argument("--output", type=str, default="data/processed/feature_importance.csv")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    try:
        run_feature_importance_analysis(args.data, args.target, args.output)
    except Exception as e:
        logger.error(f"Feature importance failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
