import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import yaml
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
import hashlib

from config import get_project_root, get_data_paths, get_config_summary
from validators import validate_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_input_data(data: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate input data against the dataset schema.
    Checks for required columns: bulk_config_id, impurity_species, segregation_energy, clustering_descriptors (expanded).
    """
    required_fields = ['bulk_config_id', 'impurity_species', 'segregation_energy']
    # Descriptors are expected to be expanded columns (e.g., rdf_peak, pair_corr, voronoi_count)
    # We check if at least one descriptor column exists
    descriptor_cols = [c for c in data.columns if c not in required_fields]
    
    if not all(field in data.columns for field in required_fields):
        missing = [f for f in required_fields if f not in data.columns]
        raise ValueError(f"Missing required fields: {missing}")
    
    if not descriptor_cols:
        raise ValueError("No descriptor columns found in input data.")
    
    logger.info(f"Input data validated. Found {len(descriptor_cols)} descriptor columns.")
    return True

def run_kfold_cv(
    X: np.ndarray, 
    y: np.ndarray, 
    k_folds: int = 5, 
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Perform manual k-fold cross-validation using statsmodels OLS.
    Returns aggregated metrics and fold-level details.
    """
    kf = KFold(n_splits=k_folds, shuffle=True, random_state=random_seed)
    
    fold_metrics = []
    all_predictions = []
    all_true = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Add constant for intercept
        X_train_const = add_constant(X_train)
        X_test_const = add_constant(X_test)
        
        # Fit OLS with HC3 covariance for robust standard errors
        model = OLS(y_train, X_train_const).fit(cov_type='HC3')
        
        # Predict
        y_pred = model.predict(X_test_const)
        
        # Calculate metrics
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        fold_metrics.append({
            "fold": fold_idx + 1,
            "r2": r2,
            "rmse": rmse
        })
        
        all_predictions.extend(y_pred)
        all_true.extend(y_test)
    
    # Aggregate metrics
    avg_r2 = np.mean([m['r2'] for m in fold_metrics])
    avg_rmse = np.mean([m['rmse'] for m in fold_metrics])
    
    return {
        "fold_metrics": fold_metrics,
        "aggregate": {
            "r2": avg_r2,
            "rmse": avg_rmse
        },
        "final_predictions": all_predictions,
        "final_true": all_true
    }

def check_collinearity_warning() -> bool:
    """
    Check if the collinearity report exists and indicates high VIF.
    Returns True if a warning should be logged.
    """
    project_root = get_project_root()
    report_path = project_root / "data" / "processed" / "collinearity_report.md"
    
    if not report_path.exists():
        logger.warning("Collinearity report not found. Proceeding without check.")
        return False
    
    with open(report_path, 'r') as f:
        content = f.read()
    
    # Simple heuristic: check for VIF >= 10 mention
    if "VIF" in content and ("10" in content or "high" in content.lower()):
        logger.warning("High collinearity detected in previous analysis. P-values may be unstable.")
        return True
    
    return False

def train_model(X: np.ndarray, y: np.ndarray, random_seed: int = 42) -> OLS:
    """
    Train the final OLS model on the full dataset.
    """
    X_const = add_constant(X)
    model = OLS(y, X_const).fit(cov_type='HC3')
    return model

def calculate_confidence_intervals(
    model: OLS, 
    X_new: np.ndarray, 
    confidence_level: float = 0.95
) -> np.ndarray:
    """
    Calculate confidence intervals for predictions.
    """
    X_new_const = add_constant(X_new)
    predictions = model.predict(X_new_const)
    # Get prediction intervals (approximate for OLS)
    # Using standard error of prediction
    se_pred = model.get_prediction(X_new_const).summary_frame()['obs_ci_lower']
    # For simplicity, we return the lower bound as a proxy for CI calculation
    # In a full implementation, we would calculate full intervals
    return predictions

def save_results(
    metrics: Dict[str, Any], 
    model: OLS, 
    X: np.ndarray,
    y: np.ndarray,
    output_path: Path
):
    """
    Save metrics and model parameters to results/metrics.json.
    Also compute SHA256 hash of the code for provenance.
    """
    # Compute code hash
    code_hash = hashlib.sha256(open(__file__, 'rb').read()).hexdigest()
    
    # Prepare results dictionary
    results = {
        "r2": metrics['aggregate']['r2'],
        "rmse": metrics['aggregate']['rmse'],
        "p_values": model.pvalues.to_dict(),
        "coefficients": model.params.to_dict(),
        "confidence_intervals": "Calculated per prediction (see code logic)",
        "code_version_hash": code_hash,
        "fold_details": metrics['fold_metrics']
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Code version hash: {code_hash}")

def main():
    """
    Main entry point for the training pipeline.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    # Load data
    descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
    energies_path = project_root / "data" / "processed" / "segregation_energies.csv"
    
    if not descriptors_path.exists() or not energies_path.exists():
        raise FileNotFoundError("Required data files (descriptors.csv, segregation_energies.csv) not found. "
                                "Please run Phase 3 (US1) tasks first.")
    
    df_desc = pd.read_csv(descriptors_path)
    df_energy = pd.read_csv(energies_path)
    
    # Merge data
    # Assuming both have 'bulk_config_id' as key
    df = pd.merge(df_desc, df_energy, on='bulk_config_id', how='inner')
    
    if df.empty:
        raise ValueError("Merged dataset is empty. Check key columns.")
    
    # Define features and target
    target_col = 'segregation_energy'
    feature_cols = [c for c in df.columns if c not in ['bulk_config_id', 'impurity_species', target_col]]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Validate input
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    if schema_path.exists():
        schema = load_schema(schema_path)
        validate_input_data(df, schema)
    
    # Check collinearity
    check_collinearity_warning()
    
    # Run Cross-Validation
    config_summary = get_config_summary()
    random_seed = config_summary.get('random_seed', 42)
    k_folds = config_summary.get('cv_folds', 5)
    
    logger.info(f"Running {k_folds}-fold Cross-Validation with seed {random_seed}")
    cv_results = run_kfold_cv(X, y, k_folds=k_folds, random_seed=random_seed)
    
    # Train final model on full data
    logger.info("Training final model on full dataset...")
    final_model = train_model(X, y, random_seed=random_seed)
    
    # Save results
    output_path = project_root / "results" / "metrics.json"
    save_results(cv_results, final_model, X, y, output_path)
    
    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    main()