import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import sys

# Add project root to path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import ensure_directories
from env_config import get_processed_data_path, get_models_artifacts_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for model hyperparameters per spec
RF_MAX_DEPTH = 10
RF_N_ESTIMATORS = 100
GP_KERNEL = C(1.0, (1e-3, 1e3)) * RBF(10.0, (1e-2, 1e2))

def load_preprocessed_data(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load preprocessed data from parquet."""
    if data_dir is None:
        data_dir = get_processed_data_path()
    
    input_path = data_dir / "preprocessed_data.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}. "
                                "Run T014c preprocessing task first.")
    
    logger.info(f"Loading preprocessed data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Ensure required columns exist
    required_cols = ['date', 'gsn', 'tsi', 'cycle_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in preprocessed data: {missing}")
    
    # Filter out rows with missing cycle_id or target values (pre-satellite gaps might not have TSI)
    df = df.dropna(subset=['cycle_id', 'tsi', 'gsn'])
    logger.info(f"Loaded {len(df)} rows for training")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features (X) and targets (y) for training.
    
    Features:
    - gsn: Grouped Sunspot Number
    - cycle_id: Categorical integer representing the solar cycle (FR-003)
    
    Target:
    - tsi: Total Solar Irradiance
    """
    # Ensure cycle_id is treated as a feature (integer)
    X = df[['gsn', 'cycle_id']].copy()
    y = df['tsi'].copy()
    
    logger.info(f"Prepared features: {X.shape}, target: {y.shape}")
    return X, y

def train_random_forest(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """Train a Random Forest model with specified hyperparameters."""
    logger.info(f"Training Random Forest (max_depth={RF_MAX_DEPTH}, n_estimators={RF_N_ESTIMATORS})")
    model = RandomForestRegressor(
        max_depth=RF_MAX_DEPTH,
        n_estimators=RF_N_ESTIMATORS,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)
    logger.info("Random Forest training complete")
    return model

def train_gaussian_process(X: pd.DataFrame, y: pd.Series) -> GaussianProcessRegressor:
    """Train a Gaussian Process model with RBF kernel."""
    logger.info("Training Gaussian Process (RBF kernel)")
    kernel = GP_KERNEL
    model = GaussianProcessRegressor(kernel=kernel, random_state=42, n_restarts_optimizer=10)
    model.fit(X, y)
    logger.info("Gaussian Process training complete")
    return model

def evaluate_model(model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
    """Evaluate model and return RMSE and R2."""
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    return {"rmse": float(rmse), "r2": float(r2)}

def run_loco_cv(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Leave-One-Cycle-Out Cross-Validation.
    
    Strategy:
    1. Identify unique cycles.
    2. For each cycle, train on all OTHER cycles, validate on the held-out cycle.
    3. Calculate RMSE and R2 for the held-out cycle.
    4. Determine the best model based on mean performance.
    """
    cycles = sorted(df['cycle_id'].unique())
    logger.info(f"Running LOCO CV on {len(cycles)} cycles: {cycles}")
    
    rf_results = []
    gp_results = []
    
    for cycle in cycles:
        logger.info(f"--- Holdout Cycle: {cycle} ---")
        
        # Split data
        train_mask = df['cycle_id'] != cycle
        test_mask = df['cycle_id'] == cycle
        
        X_train, y_train = prepare_features(df[train_mask])
        X_test, y_test = prepare_features(df[test_mask])
        
        if len(X_test) == 0:
            logger.warning(f"No data for cycle {cycle}, skipping.")
            continue
        
        # Train RF
        rf_model = train_random_forest(X_train, y_train)
        rf_metrics = evaluate_model(rf_model, X_test, y_test)
        rf_metrics['cycle'] = int(cycle)
        rf_results.append(rf_metrics)
        
        # Train GP
        gp_model = train_gaussian_process(X_train, y_train)
        gp_metrics = evaluate_model(gp_model, X_test, y_test)
        gp_metrics['cycle'] = int(cycle)
        gp_results.append(gp_metrics)
    
    # Aggregate results
    rf_avg_rmse = np.mean([r['rmse'] for r in rf_results])
    gp_avg_rmse = np.mean([r['rmse'] for r in gp_results])
    
    rf_avg_r2 = np.mean([r['r2'] for r in rf_results])
    gp_avg_r2 = np.mean([r['r2'] for r in gp_results])
    
    # Model Selection Rationale
    if rf_avg_rmse < gp_avg_rmse:
        selected_model = "RandomForest"
        rationale = f"RF (RMSE={rf_avg_rmse:.4f}) outperformed GP (RMSE={gp_avg_rmse:.4f})"
    else:
        selected_model = "GaussianProcess"
        rationale = f"GP (RMSE={gp_avg_rmse:.4f}) outperformed RF (RMSE={rf_avg_rmse:.4f})"
    
    report = {
        "methodology": "Leave-One-Cycle-Out (LOCO) Cross-Validation",
        "total_cycles": len(cycles),
        "random_forest": {
            "avg_rmse": float(rf_avg_rmse),
            "avg_r2": float(rf_avg_r2),
            "per_cycle_metrics": rf_results
        },
        "gaussian_process": {
            "avg_rmse": float(gp_avg_rmse),
            "avg_r2": float(gp_avg_r2),
            "per_cycle_metrics": gp_results
        },
        "model_selection": {
            "selected_model": selected_model,
            "rationale": rationale
        }
    }
    
    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save CV report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def save_model_artifacts(models_dir: Path, rf_model: Any, gp_model: Any) -> Dict[str, str]:
    """Save trained models to artifacts directory."""
    models_dir.mkdir(parents=True, exist_ok=True)
    
    rf_path = models_dir / "random_forest_model.joblib"
    gp_path = models_dir / "gaussian_process_model.joblib"
    
    joblib.dump(rf_model, rf_path)
    joblib.dump(gp_model, gp_path)
    
    logger.info(f"Models saved: {rf_path}, {gp_path}")
    return {"random_forest": str(rf_path), "gaussian_process": str(gp_path)}

def run_training_pipeline(data_dir: Optional[Path] = None, models_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Orchestrate the full training pipeline.
    
    1. Load preprocessed data.
    2. Run LOCO CV to generate metrics and select best model.
    3. Retrain the selected model (or both) on the FULL dataset for production use.
    4. Save artifacts and report.
    """
    if data_dir is None:
        data_dir = get_processed_data_path()
    if models_dir is None:
        models_dir = get_models_artifacts_path()
    
    ensure_directories()
    
    # 1. Load Data
    df = load_preprocessed_data(data_dir)
    
    # 2. Run LOCO CV
    logger.info("Starting LOCO Cross-Validation...")
    cv_report = run_loco_cv(df)
    
    # 3. Save Report
    report_path = data_dir / "cv_report.json"
    save_report(cv_report, report_path)
    
    # 4. Retrain on full data for final artifacts
    logger.info("Retraining final models on full dataset...")
    X_full, y_full = prepare_features(df)
    
    final_rf = train_random_forest(X_full, y_full)
    final_gp = train_gaussian_process(X_full, y_full)
    
    # 5. Save Artifacts
    artifact_paths = save_model_artifacts(models_dir, final_rf, final_gp)
    
    return {
        "report": str(report_path),
        **artifact_paths
    }

def main():
    """Entry point for the training script."""
    logger.info("Starting Solar Irradiance Model Training (T015)")
    try:
        paths = run_training_pipeline()
        logger.info(f"Pipeline completed successfully. Artifacts: {paths}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
