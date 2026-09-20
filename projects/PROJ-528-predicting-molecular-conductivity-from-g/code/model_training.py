import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from code.config import SEED, TARGET_VAR, VIF_THRESHOLD
from code.scaffold_split import scaffold_split
from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def apply_log_transformation(y: pd.Series) -> pd.Series:
    return np.log(y + 1e-9)

def select_target_variable(df: pd.DataFrame, target_candidates: List[str]) -> str:
    for candidate in target_candidates:
        if candidate in df.columns:
            logger.info(f"Using {candidate} as target variable.")
            return candidate
    raise ValueError(f"No valid target variable found in {target_candidates}")

def train_models(X: np.ndarray, y: pd.Series, seed: int) -> Tuple[RandomForestRegressor, GradientBoostingRegressor]:
    rf = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed)
    gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=seed)
    rf.fit(X, y)
    gb.fit(X, y)
    return rf, gb

def run_cross_validation(model, X: np.ndarray, y: pd.Series, cv: int = 5) -> List[float]:
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    return scores.tolist()

def save_model_results(results: Dict[str, Any], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Model results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train models on processed data.")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv")
    parser.add_argument("--output", type=str, default="data/processed/model_results.json")
    args = parser.parse_args()

    setup_logging()
    logger.info("Starting Model Training")

    df = pd.read_csv(args.data)
    target_col = select_target_variable(df, ['conductivity', 'HOMO_LUMO_gap'])
    y = df[target_col]
    y_log = apply_log_transformation(y)

    feature_cols = [c for c in df.columns if c not in ['smiles', target_col, 'valid', 'error_msg']]
    X = df[feature_cols].values

    rf, gb = train_models(X, y_log, SEED)

    # Cross-validation
    cv_rf = run_cross_validation(rf, X, y_log)
    cv_gb = run_cross_validation(gb, X, y_log)

    # Train/Test split for final metrics
    X_train, X_test, y_train, y_test = train_test_split(X, y_log, test_size=0.2, random_state=SEED)
    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)
    r2_rf = r2_score(y_test, rf.predict(X_test))
    r2_gb = r2_score(y_test, gb.predict(X_test))

    results = {
        "target_variable": target_col,
        "rf_r2": r2_rf,
        "gb_r2": r2_gb,
        "cv_rf_mean": np.mean(cv_rf),
        "cv_gb_mean": np.mean(cv_gb)
    }
    save_model_results(results, args.output)

if __name__ == "__main__":
    main()
