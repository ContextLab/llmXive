import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Import utilities from infrastructure
from infrastructure.path_utils import get_project_root, ensure_dir

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_git_hash() -> str:
    """Get the current git commit hash."""
    try:
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "file_not_found"

def ensure_output_directories() -> None:
    """Ensure all required output directories exist."""
    project_root = get_project_root()
    dirs = [
        "data/validation",
        "data/validation/external",
        "data/state"
    ]
    for d in dirs:
        ensure_dir(os.path.join(project_root, d))

def load_json_file(file_path: str) -> Dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: str, data: Dict) -> None:
    """Save a dictionary to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_file(file_path: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path)

def save_csv_file(file_path: str, df: pd.DataFrame) -> None:
    """Save a DataFrame to a CSV file."""
    df.to_csv(file_path, index=False)

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load processed features and targets."""
    project_root = get_project_root()
    features_path = os.path.join(project_root, "data/processed/features.csv")
    targets_path = os.path.join(project_root, "data/processed/targets.csv")
    return load_csv_file(features_path), load_csv_file(targets_path)

def load_models() -> Dict[str, Any]:
    """Load trained models."""
    project_root = get_project_root()
    model_path = os.path.join(project_root, "data/processed/final_models.pkl")
    if os.path.exists(model_path):
        import pickle
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    return {}

def compute_vif(features: pd.DataFrame) -> pd.Series:
    """Compute Variance Inflation Factor for features."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    X = features.values
    vif_data = pd.Series([variance_inflation_factor(X, i) for i in range(X.shape[1])], index=features.columns)
    return vif_data

def compute_permutation_stability(model, X: pd.DataFrame, y: pd.Series, n_runs: int = 10) -> Dict[str, List[float]]:
    """Compute permutation importance stability across multiple runs."""
    from sklearn.inspection import permutation_importance
    stability = {}
    for _ in range(n_runs):
        result = permutation_importance(model, X, y, n_repeats=10, random_state=42)
        for i, name in enumerate(X.columns):
            if name not in stability:
                stability[name] = []
            stability[name].append(result.importances_mean[i])
    return stability

def flag_collinearity(vif_series: pd.Series, threshold: float = 5.0) -> List[str]:
    """Flag features with VIF above threshold."""
    return [col for col, vif in vif_series.items() if vif > threshold]

def generate_ranked_list(importance_scores: Dict[str, float]) -> List[Tuple[str, float]]:
    """Generate a ranked list of features by importance."""
    return sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)

def run_sensitivity_analysis(model, X: pd.DataFrame, y: pd.Series, thresholds: List[float]) -> pd.DataFrame:
    """Run sensitivity analysis over different thresholds."""
    results = []
    for thresh in thresholds:
        # Placeholder logic: adjust based on actual model type
        predictions = model.predict(X)
        # Example: binary classification thresholding
        binary_preds = (predictions > thresh).astype(int)
        binary_true = (y > thresh).astype(int)
        tp = ((binary_preds == 1) & (binary_true == 1)).sum()
        fp = ((binary_preds == 1) & (binary_true == 0)).sum()
        fn = ((binary_preds == 0) & (binary_true == 1)).sum()
        tn = ((binary_preds == 0) & (binary_true == 0)).sum()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        results.append({'threshold': thresh, 'fpr': fpr, 'fnr': fnr})
    return pd.DataFrame(results)

def load_data_source_flag() -> Dict:
    """Load the data source flag from state."""
    project_root = get_project_root()
    state_path = os.path.join(project_root, "data/state/data_source.json")
    if os.path.exists(state_path):
        return load_json_file(state_path)
    return {"status": "unknown", "source": "unknown"}

def load_mock_dftb_exclusions() -> Dict:
    """Load mock DFTB exclusions log."""
    project_root = get_project_root()
    exclusions_path = os.path.join(project_root, "data/state/mock_dftb_exclusions.json")
    if os.path.exists(exclusions_path):
        return load_json_file(exclusions_path)
    return {"exclusion_count": 0}

def check_external_data_exists() -> Optional[pd.DataFrame]:
    """Scan data/validation/external/ for valid datasets."""
    project_root = get_project_root()
    external_dir = os.path.join(project_root, "data/validation/external")
    if not os.path.exists(external_dir):
        return None
    
    valid_extensions = ['.csv', '.json']
    for filename in os.listdir(external_dir):
        if any(filename.endswith(ext) for ext in valid_extensions):
            file_path = os.path.join(external_dir, filename)
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        df = pd.DataFrame(data)
                
                # Basic validation: check for required columns
                required_cols = ['defect_type', 'defect_density', 'conductivity']
                if all(col in df.columns for col in required_cols):
                    logger.info(f"Found valid external dataset: {filename}")
                    return df
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")
    return None

def run_external_validation(external_df: pd.DataFrame, models: Dict[str, Any]) -> Dict:
    """Run validation against external dataset."""
    results = {"status": "validated", "metrics": {}}
    # Placeholder: implement actual validation logic based on model types
    for target, model in models.items():
        if target in external_df.columns and 'defect_density' in external_df.columns:
            # Example: simple correlation check
            preds = model.predict(external_df[['defect_density']])
            actual = external_df[target]
            from sklearn.metrics import r2_score, mean_absolute_error
            r2 = r2_score(actual, preds) if len(actual) > 1 else 0.0
            mae = mean_absolute_error(actual, preds) if len(actual) > 0 else 0.0
            results["metrics"][target] = {"r2": r2, "mae": mae}
    return results

def run_validation_analysis() -> Dict:
    """Main validation analysis logic for T030."""
    ensure_output_directories()
    project_root = get_project_root()
    
    # Load data source flag
    data_source = load_data_source_flag()
    source_type = data_source.get("source", "unknown")
    
    # Determine exclusion count
    exclusion_count = 0
    if source_type == "synthetic":
        exclusion_count = 0
    else:
        mock_exclusions = load_mock_dftb_exclusions()
        exclusion_count = mock_exclusions.get("exclusion_count", 0)
    
    # Check for external data
    external_df = check_external_data_exists()
    
    validation_report = {
        "status": "NO_EXTERNAL_DATA",
        "method": "internal_only",
        "exclusion_count": exclusion_count,
        "data_source": source_type,
        "external_data_found": False,
        "validation_metrics": {}
    }
    
    if external_df is not None:
        # Load models and run validation
        models = load_models()
        if models:
            validation_result = run_external_validation(external_df, models)
            validation_report["status"] = "validated"
            validation_report["external_data_found"] = True
            validation_report["validation_metrics"] = validation_result.get("metrics", {})
        else:
            validation_report["status"] = "no_models_available"
            validation_report["external_data_found"] = True
    else:
        logger.info("No external data found. Using internal validation only.")
    
    # Save validation report
    report_path = os.path.join(project_root, "data/validation/Validation_Report.json")
    save_json_file(report_path, validation_report)
    logger.info(f"Validation report saved to {report_path}")
    
    return validation_report

def main():
    """Main entry point for T030."""
    logger.info("Starting T030: External Validation Logic")
    try:
        result = run_validation_analysis()
        logger.info(f"T030 completed successfully. Status: {result['status']}")
        return 0
    except Exception as e:
        logger.error(f"T030 failed: {e}")
        raise

if __name__ == "__main__":
    main()