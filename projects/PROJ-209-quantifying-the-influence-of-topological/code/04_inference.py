import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Infrastructure imports (shared utilities)
from infrastructure.path_utils import get_project_root, ensure_dir
from infrastructure.error_handler import exponential_backoff_retry

# Local imports (if any specific helpers exist in other files, but we rely on standard libs mostly)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return get_project_root()

def ensure_output_directories():
    """Ensure all required output directories exist."""
    dirs = [
        'data/raw',
        'data/processed',
        'data/state',
        'data/validation',
        'figures'
    ]
    project_root = get_project_root()
    for d in dirs:
        ensure_dir(d)

def get_git_hash() -> str:
    """Get the current git commit hash."""
    try:
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json_file(file_path: str) -> Dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: str, data: Dict):
    """Save a dictionary to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_processed_data() -> pd.DataFrame:
    """
    Load processed features and targets.
    Expects data/processed/features.csv and data/processed/targets.csv.
    Merges them on index or a common ID if present.
    """
    features_path = os.path.join('data/processed', 'features.csv')
    targets_path = os.path.join('data/processed', 'targets.csv')

    if not os.path.exists(features_path) or not os.path.exists(targets_path):
        raise FileNotFoundError(f"Processed data files not found. Run T018/T020 first.")

    features = pd.read_csv(features_path)
    targets = pd.read_csv(targets_path)

    # Attempt to merge on index if no explicit ID column
    if 'id' in features.columns and 'id' in targets.columns:
        df = features.merge(targets, on='id')
    else:
        # Reset index to ensure alignment if they were saved with indices
        features = features.reset_index(drop=True)
        targets = targets.reset_index(drop=True)
        df = pd.concat([features, targets], axis=1)

    return df

def load_models() -> Dict[str, Any]:
    """
    Load trained models from data/processed.
    Expected: data/processed/model_conductivity.pkl, etc.
    Returns a dict of model instances.
    """
    import pickle
    model_files = {
        'conductivity': 'model_conductivity.pkl',
        'youngs_modulus': 'model_youngs_modulus.pkl',
        'fracture_strength': 'model_fracture_strength.pkl'
    }
    models = {}
    for name, fname in model_files.items():
        path = os.path.join('data/processed', fname)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                models[name] = pickle.load(f)
        else:
            logger.warning(f"Model file not found: {path}")
    return models

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R2 and MAPE."""
    from sklearn.metrics import r2_score
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    r2 = r2_score(y_true, y_pred)
    # Avoid division by zero in MAPE
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    return {'R2': r2, 'MAPE': mape}

def run_holdout_evaluation(models: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Dict]:
    """Evaluate models on holdout set."""
    # Implementation placeholder for T024
    results = {}
    for name, model in models.items():
        # Assuming 'target_<name>' is the column in data
        target_col = f'target_{name}'
        if target_col in data.columns:
            y_true = data[target_col]
            y_pred = model.predict(data.drop(columns=[target_col])) # Simplified
            results[name] = calculate_metrics(y_true, y_pred)
    return results

def compute_permutation_p_values(model, X: np.ndarray, y: np.ndarray, n_permutations: int = 1000) -> Dict[str, float]:
    """Compute p-values for feature importance via permutation."""
    from sklearn.inspection import permutation_importance
    base_score = model.score(X, y)
    results = permutation_importance(model, X, y, n_repeats=n_permutations, random_state=42, scoring='r2')
    # Simplified p-value calculation: proportion of permuted scores >= base score
    # Note: In a rigorous setting, this requires a null distribution construction.
    # Here we approximate significance based on the distribution of importance scores.
    importance = results.importances_mean
    std_dev = results.importances_std
    # Heuristic p-value: if importance is significantly > 0
    # Using a t-test approximation or simple threshold
    p_values = {}
    for i, feat in enumerate(X.columns if hasattr(X, 'columns') else range(len(importance))):
        feat_name = str(feat)
        if std_dev[i] > 0:
            z_score = importance[i] / std_dev[i]
            # Approximate p-value from z-score (two-tailed)
            import scipy.stats as stats
            p_val = 2 * (1 - stats.norm.cdf(abs(z_score)))
        else:
            p_val = 1.0 if importance[i] <= 0 else 0.0
        p_values[feat_name] = p_val
    return p_values

def apply_benjamini_hochberg(p_values: Dict[str, float], q: float = 0.05) -> Dict[str, bool]:
    """Apply Benjamini-Hochberg FDR control."""
    sorted_items = sorted(p_values.items(), key=lambda x: x[1])
    n = len(sorted_items)
    significant = {}
    for i, (feat, p_val) in enumerate(sorted_items):
        threshold = (i + 1) / n * q
        significant[feat] = p_val <= threshold
    return significant

def rank_features(importance_scores: Dict[str, float]) -> List[Tuple[str, float]]:
    """Rank features by importance score."""
    return sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)

def run_sensitivity_analysis(models: Dict[str, Any], data: pd.DataFrame) -> pd.DataFrame:
    """Sweep decision cutoffs and report FPR/FNR."""
    # Placeholder for T026 logic
    thresholds = ['low', 'medium', 'high']
    results = []
    for thresh in thresholds:
        # Logic to calculate FPR/FNR based on threshold
        results.append({
            'threshold': thresh,
            'FPR': 0.1, # Placeholder
            'FNR': 0.2  # Placeholder
        })
    return pd.DataFrame(results)

def run_confounding_control(data: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    T027a: Confounding Control Configuration.
    
    Checks for presence of 'synthesis_method' or 'grain_size' columns.
    - If Present: Configure stratified CV folds by these variables.
    - If Absent: Check for *any* other available confounders. If found, configure them 
      as linear terms (covariates).
    - If No Confounders: Log a limitation.
    
    Outputs:
      - data/processed/confounding_config.json
      - data/processed/confounding_report.json
    """
    config = {
        "strategy": "none",
        "stratification_columns": [],
        "covariate_columns": [],
        "notes": ""
    }
    report = {
        "confounders_found": False,
        "strategy_applied": "none",
        "limitation": None,
        "verification_status": "pending"
    }

    available_columns = set(data.columns)
    primary_confounders = {'synthesis_method', 'grain_size'}
    
    # Check for primary confounders
    found_primary = primary_confounders.intersection(available_columns)
    
    if found_primary:
        config["strategy"] = "stratified_cv"
        config["stratification_columns"] = list(found_primary)
        report["confounders_found"] = True
        report["strategy_applied"] = "stratified_cv"
        report["notes"] = f"Stratified CV configured using columns: {list(found_primary)}"
        logger.info(f"Primary confounders found: {found_primary}. Configuring stratified CV.")
    else:
        # Check for other potential confounders (heuristic: categorical or low cardinality numeric)
        # For this task, we assume any column not in features/targets that looks like a category
        # Since we don't have a full schema here, we scan for common names or low cardinality
        potential_confounders = []
        for col in available_columns:
            if col not in ['id', 'defect_type', 'defect_density']: # Exclude known predictors
                # Simple heuristic: if it's object/string or has few unique values
                if data[col].dtype == 'object' or data[col].nunique() < 10:
                    potential_confounders.append(col)
        
        if potential_confounders:
            config["strategy"] = "covariate_adjustment"
            config["covariate_columns"] = potential_confounders
            report["confounders_found"] = True
            report["strategy_applied"] = "covariate_adjustment"
            report["notes"] = f"No primary confounders found. Using covariates: {potential_confounders}."
            logger.info(f"Using covariate adjustment with: {potential_confounders}")
            # Verification note: Linear terms may not capture non-linear confounding
            report["verification_status"] = "assumed_sufficient_linear"
        else:
            config["strategy"] = "none"
            report["confounders_found"] = False
            report["strategy_applied"] = "none"
            report["limitation"] = "No confounders detected. Results may be subject to unobserved confounding bias."
            report["verification_status"] = "no_confounders"
            logger.warning("No confounders detected. Proceeding without adjustment.")

    # Save outputs
    config_path = os.path.join('data/processed', 'confounding_config.json')
    report_path = os.path.join('data/processed', 'confounding_report.json')
    
    save_json_file(config_path, config)
    save_json_file(report_path, report)
    
    logger.info(f"Confounding configuration saved to {config_path}")
    logger.info(f"Confounding report saved to {report_path}")
    
    return config, report

def run_inference_analysis():
    """Main entry point for inference analysis."""
    ensure_output_directories()
    logger.info("Starting Inference Analysis (T027a + others)")
    
    # T027a: Confounding Control
    try:
        data = load_processed_data()
        config, report = run_confounding_control(data)
        logger.info("Confounding control configuration complete.")
    except FileNotFoundError as e:
        logger.error(f"Could not load processed data for confounding check: {e}")
        # Create empty config/report if data missing to prevent crash, but log error
        config = {"strategy": "error", "notes": "Data not found"}
        report = {"error": str(e)}
        save_json_file('data/processed/confounding_config.json', config)
        save_json_file('data/processed/confounding_report.json', report)

def main():
    """Main function to run the inference pipeline."""
    run_inference_analysis()

if __name__ == "__main__":
    main()