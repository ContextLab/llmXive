import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Import shared utilities from infrastructure and other modules as per API surface
from infrastructure.path_utils import get_project_root, ensure_dir
from infrastructure.error_handler import exponential_backoff_retry

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_git_hash() -> str:
    try:
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(filepath: str) -> str:
    import hashlib
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "file_missing"

def ensure_output_directories() -> None:
    root = get_project_root()
    dirs = [
        "data/raw", "data/processed", "data/state", "data/validation",
        "data/validation/external", "figures"
    ]
    for d in dirs:
        ensure_dir(os.path.join(root, d))

def load_json_file(filepath: str) -> Any:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Any) -> None:
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_csv_file(filepath: str) -> List[Dict[str, str]]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv_file(filepath: str, data: List[Dict[str, Any]]) -> None:
    ensure_dir(os.path.dirname(filepath))
    if not data:
        # Write empty file with headers if needed, or just touch
        with open(filepath, 'w', encoding='utf-8') as f:
            pass
        return
    fieldnames = data[0].keys()
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    root = get_project_root()
    features_path = os.path.join(root, "data/processed/features.csv")
    targets_path = os.path.join(root, "data/processed/targets.csv")
    if not os.path.exists(features_path) or not os.path.exists(targets_path):
        raise FileNotFoundError("Processed data files not found. Run T018/T019 first.")
    return pd.read_csv(features_path), pd.read_csv(targets_path)

def load_models() -> Dict[str, Any]:
    root = get_project_root()
    model_path = os.path.join(root, "data/processed/final_models.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError("Final models not found. Run T021 first.")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def compute_vif(features_df: pd.DataFrame) -> Dict[str, float]:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    if features_df.empty:
        return {}
    X = features_df.select_dtypes(include=[np.number])
    if X.shape[1] == 0:
        return {}
    vif_data = {}
    for i, col in enumerate(X.columns):
        try:
            vif_data[col] = variance_inflation_factor(X.values, i)
        except Exception:
            vif_data[col] = np.inf
    return vif_data

def compute_permutation_stability(model: Any, X: pd.DataFrame, y: pd.Series, n_runs: int = 10) -> Dict[str, float]:
    # Placeholder for stability computation if needed in future
    return {"stability_score": 0.0}

def flag_collinearity(vif_results: Dict[str, float], threshold: float = 5.0) -> List[str]:
    return [col for col, vif in vif_results.items() if vif > threshold]

def generate_ranked_list(importance_scores: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)

def run_sensitivity_analysis(model: Any, X: pd.DataFrame, y: pd.Series, thresholds: List[float]) -> pd.DataFrame:
    # Placeholder for sensitivity analysis logic
    data = []
    for t in thresholds:
        data.append({"threshold": t, "fpr": 0.0, "fnr": 0.0})
    return pd.DataFrame(data)

def load_data_source_flag() -> Dict[str, Any]:
    root = get_project_root()
    path = os.path.join(root, "data/state/data_source.json")
    if not os.path.exists(path):
        return {"status": "unknown", "source": "unknown"}
    return load_json_file(path)

def load_mock_dftb_exclusions() -> int:
    root = get_project_root()
    path = os.path.join(root, "data/state/mock_dftb_exclusions.json")
    if not os.path.exists(path):
        return 0
    try:
        data = load_json_file(path)
        return data.get("exclusions", 0)
    except Exception:
        return 0

def check_external_data_exists(external_dir: str) -> Optional[str]:
    """
    Scans the external directory for valid CSV or JSON files.
    Returns the path to the first valid file found, or None if none exist.
    """
    if not os.path.exists(external_dir):
        return None
    for filename in os.listdir(external_dir):
        if filename.endswith('.csv') or filename.endswith('.json'):
            filepath = os.path.join(external_dir, filename)
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                    # Basic validation: must have at least one row and one column
                    if df.shape[0] > 0 and df.shape[1] > 0:
                        return filepath
                elif filename.endswith('.json'):
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return filepath
            except Exception as e:
                logger.warning(f"Skipping invalid external file {filename}: {e}")
                continue
    return None

def run_external_validation(external_data_path: str, models: Dict[str, Any], features: pd.DataFrame, targets: pd.Series) -> Dict[str, Any]:
    """
    Runs validation against an external dataset.
    Since the structure of external data is unknown, we attempt to align columns
    with the training features and compute R2 if possible.
    """
    result = {
        "status": "pending",
        "method": "external",
        "metrics": {}
    }

    try:
        if external_data_path.endswith('.csv'):
            ext_df = pd.read_csv(external_data_path)
        else:
            with open(external_data_path, 'r') as f:
                ext_df = pd.DataFrame(json.load(f))

        # Attempt to find target column (common names: conductivity, youngs_modulus, fracture_strength)
        target_col = None
        possible_targets = ['conductivity', 'youngs_modulus', 'fracture_strength', 'target', 'y']
        for t in possible_targets:
            if t in ext_df.columns:
                target_col = t
                break

        if not target_col:
            result["status"] = "skipped"
            result["reason"] = "No recognizable target column in external data"
            return result

        # Align features
        available_features = [c for c in ext_df.columns if c in features.columns]
        if not available_features:
            result["status"] = "skipped"
            result["reason"] = "No matching feature columns found in external data"
            return result

        X_ext = ext_df[available_features].dropna()
        y_ext = ext_df.loc[X_ext.index, target_col].dropna()

        # Re-index to match
        common_idx = X_ext.index.intersection(y_ext.index)
        X_ext = X_ext.loc[common_idx]
        y_ext = y_ext.loc[common_idx]

        if X_ext.empty:
            result["status"] = "skipped"
            result["reason"] = "No common indices after alignment"
            return result

        # Predict
        predictions = {}
        for name, model in models.items():
            try:
                pred = model.predict(X_ext)
                # Calculate R2
                from sklearn.metrics import r2_score
                r2 = r2_score(y_ext, pred)
                predictions[name] = {"r2": float(r2), "samples": len(y_ext)}
            except Exception as e:
                predictions[name] = {"error": str(e)}

        result["status"] = "success"
        result["metrics"] = predictions
        result["external_file"] = external_data_path

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)

    return result

def run_validation_analysis() -> Dict[str, Any]:
    """
    Main logic for T030: External Validation Logic.
    1. Read data_source.json.
    2. Scan data/validation/external/ for valid datasets.
    3. If found, run validation. If not, report NO_EXTERNAL_DATA.
    4. Determine exclusion_count based on source type.
    5. Write Validation_Report.json.
    """
    root = get_project_root()
    ensure_output_directories()

    # 1. Read data source flag
    source_info = load_data_source_flag()
    data_source = source_info.get("source", "unknown")
    logger.info(f"Detected data source: {data_source}")

    # 2. Scan for external data
    external_dir = os.path.join(root, "data/validation/external")
    external_path = check_external_data_exists(external_dir)

    report = {
        "task_id": "T030",
        "timestamp": pd.Timestamp.now().isoformat(),
        "git_hash": get_git_hash(),
        "data_source": data_source,
        "status": "NO_EXTERNAL_DATA",
        "method": "internal_only",
        "exclusion_count": 0,
        "validation_results": None
    }

    # Determine exclusion count
    if data_source == "synthetic":
        report["exclusion_count"] = 0
    else:
        # Real data path: check mock_dftb_exclusions.json
        exc_count = load_mock_dftb_exclusions()
        report["exclusion_count"] = exc_count

    if external_path:
        logger.info(f"External data found: {external_path}")
        try:
            # Load models and data for validation
            models = load_models()
            features, targets = load_processed_data()
            
            # Run validation
            validation_res = run_external_validation(external_path, models, features, targets)
            
            report["status"] = "completed"
            report["method"] = "external"
            report["validation_results"] = validation_res
        except Exception as e:
            logger.error(f"External validation failed: {e}")
            report["status"] = "failed"
            report["error"] = str(e)
    else:
        logger.info("No external data found. Generating report with NO_EXTERNAL_DATA status.")
        # Ensure validation_results is null/None as per spec for this case
        report["validation_results"] = None

    # 5. Write report
    report_path = os.path.join(root, "data/validation/Validation_Report.json")
    save_json_file(report_path, report)
    logger.info(f"Validation report written to {report_path}")

    return report

def main():
    """Entry point for T030."""
    try:
        run_validation_analysis()
        logger.info("T030 completed successfully.")
    except Exception as e:
        logger.error(f"T030 failed: {e}")
        raise

if __name__ == "__main__":
    main()
