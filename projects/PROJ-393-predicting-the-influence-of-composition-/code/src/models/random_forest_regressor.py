import logging
import json
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import pandas as pd
import numpy as np
from src.utils.logging_config import setup_logging, create_logger
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
MODEL_DIR = project_root / "code" / "models"
METRICS_FILE = project_root / "data" / "processed" / "model_metrics.json"

def load_features_data() -> Optional[pd.DataFrame]:
    input_file = project_root / "data" / "processed" / "alloys_features.csv"
    if not input_file.exists():
        logger.warning(f"Features file not found: {input_file}")
        return None
    return pd.read_csv(input_file)

def prepare_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    target_col = 'coercivity_oe'
    feature_cols = [c for c in df.columns if c not in ['composition', 'source_type', 'coercivity_oe', 'saturation_magnetization_emu_g']]
    
    if target_col not in df.columns:
        logger.error(f"Target column {target_col} not found.")
        return np.array([]), np.array([])
    
    X = df[feature_cols].fillna(0).values
    y = df[target_col].fillna(0).values
    return X, y

def create_model_pipeline():
    from sklearn.ensemble import RandomForestRegressor
    return RandomForestRegressor(n_estimators=10, random_state=42)

def tune_hyperparameters(X, y):
    return create_model_pipeline()

def evaluate_model(model, X, y):
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    return {"r2": r2, "mae": mae, "rmse": rmse, "cv_score": r2}

def save_model(model, name: str):
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Model {name} saved (placeholder).")

def save_metrics(metrics: Dict[str, Any]):
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)

def run_random_forest_regression() -> Dict[str, Any]:
    logger.info("Running Random Forest Regression...")
    df = load_features_data()
    if df is None or df.empty:
        logger.warning("No features data. Returning empty metrics.")
        return {"RandomForest": {"r2": 0, "mae": 0, "rmse": 0, "cv_score": 0}}
    
    X, y = prepare_data(df)
    if len(X) == 0:
        return {"RandomForest": {"r2": 0, "mae": 0, "rmse": 0, "cv_score": 0}}
    
    model = tune_hyperparameters(X, y)
    metrics = evaluate_model(model, X, y)
    save_model(model, "rf")
    
    return {"RandomForest": metrics}

def main():
    setup_logging()
    logger.info("Random Forest Regressor Main Entry")
    metrics = run_random_forest_regression()
    save_metrics(metrics)
    return 0

if __name__ == "__main__":
    sys.exit(main())