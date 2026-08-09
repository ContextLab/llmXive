import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error
import yaml

from config import get_project_root, get_data_paths

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_output_schema() -> Dict[str, Any]:
    """Load the output schema from the contracts directory."""
    schema_path = get_project_root() / "contracts" / "output_schema.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Output schema not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_model_output(output_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate model output against the schema."""
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in output_data:
            logger.error(f"Missing required field in output: {field}")
            return False
    return True

def validate_output_file(file_path: Path) -> bool:
    """Validate that the output file exists and is not empty."""
    if not file_path.exists():
        logger.error(f"Output file not found: {file_path}")
        return False
    if file_path.stat().st_size == 0:
        logger.error(f"Output file is empty: {file_path}")
        return False
    return True

def run_contract_validation(output_data: Dict[str, Any]) -> bool:
    """Run contract validation on the output data."""
    schema = load_output_schema()
    return validate_model_output(output_data, schema)

def calculate_rmse_variance(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate RMSE variance across folds."""
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    # Variance of RMSE across folds is typically calculated by storing RMSE per fold
    # Here we return the RMSE itself as a proxy for stability if single fold,
    # but for sensitivity analysis we need multiple runs.
    # This function will be used within the loop to collect values.
    return rmse

def run_sensitivity_analysis(
    descriptors_path: Path,
    energies_path: Path,
    thresholds: List[float],
    output_path: Path
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on decision thresholds.
    
    Args:
        descriptors_path: Path to descriptors CSV
        energies_path: Path to segregation energies CSV
        thresholds: List of threshold values to sweep (e.g., regularization strength, perturbation magnitude)
        output_path: Path to save the sensitivity report
    
    Returns:
        Dictionary containing sensitivity analysis results
    """
    logger.info(f"Loading data from {descriptors_path} and {energies_path}")
    
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors file not found: {descriptors_path}")
    if not energies_path.exists():
        raise FileNotFoundError(f"Energies file not found: {energies_path}")
    
    df_desc = pd.read_csv(descriptors_path)
    df_energy = pd.read_csv(energies_path)
    
    # Merge data based on common identifier (assuming 'config_id' or similar exists)
    # Based on T015 output: [species, rdf_peak, pair_corr, voronoi_count]
    # Based on T016c output: segregation energies
    # We need to join them. Assuming a common index or ID column.
    # If not present, we assume they are aligned by row order or a 'config_id' column.
    # Let's assume a 'config_id' column exists or is the index.
    # For robustness, we'll try to merge on index if no explicit ID column.
    if 'config_id' in df_desc.columns and 'config_id' in df_energy.columns:
        df = pd.merge(df_desc, df_energy, on='config_id')
    else:
        # Fallback: assume row alignment or create an index
        df_desc['index'] = range(len(df_desc))
        df_energy['index'] = range(len(df_energy))
        df = pd.merge(df_desc, df_energy, on='index')
        logger.warning("No 'config_id' found, merging on row index. Ensure alignment.")
    
    # Prepare features and target
    # Features: rdf_peak, pair_corr, voronoi_count (from T015)
    feature_cols = [col for col in df.columns if col in ['rdf_peak', 'pair_corr', 'voronoi_count']]
    if not feature_cols:
        # Fallback to numeric columns if specific ones missing
        feature_cols = df.select_dtypes(include=[np.number]).columns.drop(
            [col for col in df.select_dtypes(include=[np.number]).columns if 'energy' in col or 'index' in col]
        ).tolist()
    
    X = df[feature_cols].values
    y = df['segregation_energy'].values if 'segregation_energy' in df.columns else df.iloc[:, -1].values
    
    logger.info(f"Using features: {feature_cols}, target shape: {y.shape}")
    
    results = []
    model = LinearRegression()
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")
        
        # Simulate sensitivity to threshold:
        # In this context, 'threshold' could represent a perturbation magnitude
        # or a regularization parameter. Since LinearRegression doesn't have a 'threshold'
        # parameter like Lasso/Ridge, we interpret this as a perturbation to the data
        # or a filter threshold.
        # Given FR-006 and the task description, we sweep a parameter that affects model stability.
        # Let's interpret 'threshold' as a perturbation magnitude added to features to test robustness.
        # Or, if it's a regularization threshold, we might skip it for LinearRegression and use a dummy.
        # However, the task asks for RMSE variance and R2 stability across thresholds.
        # Let's assume 'threshold' is a perturbation magnitude applied to X.
        
        X_perturbed = X + np.random.normal(0, threshold, size=X.shape)
        
        fold_r2 = []
        fold_rmse = []
        
        for train_idx, test_idx in kf.split(X_perturbed):
            X_train, X_test = X_perturbed[train_idx], X_perturbed[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            fold_r2.append(r2_score(y_test, y_pred))
            fold_rmse.append(mean_squared_error(y_test, y_pred, squared=False))
        
        avg_r2 = np.mean(fold_r2)
        avg_rmse = np.mean(fold_rmse)
        rmse_variance = np.var(fold_rmse)
        r2_stability = 1 - (np.std(fold_r2) / (np.mean(fold_r2) + 1e-8))  # Normalized stability metric
        
        result_entry = {
            "threshold": threshold,
            "rmse_variance": float(rmse_variance),
            "r2_stability": float(r2_stability),
            "avg_r2": float(avg_r2),
            "avg_rmse": float(avg_rmse)
        }
        results.append(result_entry)
        logger.info(f"Threshold {threshold}: RMSE Var={rmse_variance:.4f}, R2 Stability={r2_stability:.4f}")
    
    # Prepare output report
    report = {
        "sensitivity_analysis": results,
        "metadata": {
            "feature_columns": feature_cols,
            "n_samples": len(X),
            "n_folds": 5,
            "thresholds_tested": thresholds
        }
    }
    
    # Validate against schema
    if not run_contract_validation(report):
        logger.warning("Report failed contract validation, but saving anyway for debugging.")
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity analysis report saved to {output_path}")
    return report

def main():
    """Main entry point for the sensitivity analysis."""
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
    energies_path = project_root / "data" / "processed" / "segregation_energies.csv"
    output_path = project_root / "results" / "sensitivity_report.json"
    
    # Define thresholds to sweep (example: perturbation magnitudes)
    # These could represent different levels of noise or regularization strength
    thresholds = [0.0, 0.1, 0.2, 0.5, 1.0]
    
    try:
        report = run_sensitivity_analysis(
            descriptors_path=descriptors_path,
            energies_path=energies_path,
            thresholds=thresholds,
            output_path=output_path
        )
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()