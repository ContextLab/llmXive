"""
Data Processing Module for Quantifying Topological Defect Influence.

This module handles:
1. Loading pristine structures and defect datasets.
2. Extracting reference values (sigma_0, E_0, sigma_f_0).
3. Normalizing targets (relative changes).
4. Handling missing references and logging exclusions.
5. One-hot encoding categorical features.
6. Writing processed features, targets, and state logs.
"""
import os
import csv
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def ensure_output_directories() -> None:
    """Ensures required output directories exist."""
    dirs = [
        get_project_root() / "data" / "processed",
        get_project_root() / "data" / "state"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_git_hash() -> str:
    """Attempts to get the current git commit hash."""
    try:
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json_file(file_path: Path) -> Dict:
    """Loads a JSON file and returns its content as a dictionary."""
    if not file_path.exists():
        logger.warning(f"JSON file not found: {file_path}")
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: Dict) -> None:
    """Saves a dictionary to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def load_csv_to_dicts(file_path: Path) -> List[Dict[str, Any]]:
    """Loads a CSV file and returns a list of dictionaries."""
    if not file_path.exists():
        logger.warning(f"CSV file not found: {file_path}")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(file_path: Path, data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file with headers if fieldnames provided, else empty file
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            else:
                pass # Empty file
        return

    if not fieldnames:
        fieldnames = list(data[0].keys())

    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def parse_float_safe(value: Any, default: float = 0.0) -> float:
    """Safely parses a value to float."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def load_pristine_structures() -> List[Dict[str, Any]]:
    """Loads pristine structures from data/raw/pristine_structures.csv."""
    project_root = get_project_root()
    file_path = project_root / "data" / "raw" / "pristine_structures.csv"
    return load_csv_to_dicts(file_path)

def load_defect_dataset() -> List[Dict[str, Any]]:
    """Loads the defect dataset (real or synthetic) based on state."""
    project_root = get_project_root()
    state_file = project_root / "data" / "state" / "data_source.json"
    state = load_json_file(state_file)
    
    source_type = state.get("source_type", "real")
    holdout_filename = state.get("holdout_filename", "")
    
    # Determine which file to load
    if source_type == "real":
        file_path = project_root / "data" / "raw" / "defect_dataset_2022.csv"
    else:
        # For synthetic, we usually use the train set for processing, 
        # unless specified otherwise. The task implies processing the main dataset.
        # If the state says synthetic, the main dataset is synthetic_train.csv
        file_path = project_root / "data" / "raw" / "synthetic_train.csv"
    
    return load_csv_to_dicts(file_path)

def extract_pristine_references(pristine_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Extracts scalar reference values (sigma_0, E_0, sigma_f_0) from pristine structures.
    Returns a dict mapping material_id to references, or aggregates if needed.
    For this task, we assume we need global averages or specific material references.
    Based on the task description: "Extract scalar reference values... from pristine_structures.csv".
    We will compute global averages for graphene and MoS2 if multiple exist, 
    or specific values if keyed by material.
    Let's assume the CSV has columns: material_id, sigma_0, E_0, sigma_f_0.
    """
    sigma_0_vals = []
    E_0_vals = []
    sigma_f_0_vals = []
    
    for row in pristine_data:
        sigma_0_vals.append(parse_float_safe(row.get('sigma_0'), None))
        E_0_vals.append(parse_float_safe(row.get('E_0'), None))
        sigma_f_0_vals.append(parse_float_safe(row.get('sigma_f_0'), None))
    
    # Filter out None
    sigma_0_vals = [x for x in sigma_0_vals if x is not None]
    E_0_vals = [x for x in E_0_vals if x is not None]
    sigma_f_0_vals = [x for x in sigma_f_0_vals if x is not None]
    
    if not sigma_0_vals or not E_0_vals or not sigma_f_0_vals:
        logger.error("Missing reference values in pristine structures.")
        return {"sigma_0": 0.0, "E_0": 0.0, "sigma_f_0": 0.0}
    
    return {
        "sigma_0": sum(sigma_0_vals) / len(sigma_0_vals),
        "E_0": sum(E_0_vals) / len(E_0_vals),
        "sigma_f_0": sum(sigma_f_0_vals) / len(sigma_f_0_vals)
    }

def normalize_targets(defect_data: List[Dict[str, Any]], refs: Dict[str, float]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Computes relative changes (Delta/Ref) for conductivity, Young's modulus, fracture strength.
    Returns normalized data and list of excluded IDs.
    """
    normalized = []
    excluded_ids = []
    
    sigma_0 = refs.get("sigma_0", 0.0)
    E_0 = refs.get("E_0", 0.0)
    sigma_f_0 = refs.get("sigma_f_0", 0.0)
    
    for row in defect_data:
        row_id = row.get("id", row.get("entry_id", "unknown"))
        try:
            # Extract raw values
            sigma = parse_float_safe(row.get("conductivity"))
            E = parse_float_safe(row.get("youngs_modulus")) # Assuming column name
            sigma_f = parse_float_safe(row.get("fracture_strength")) # Assuming column name
            
            # Check for missing raw values or zero references
            if sigma_0 == 0 or E_0 == 0 or sigma_f_0 == 0:
                excluded_ids.append(row_id)
                continue
            
            if sigma is None or E is None or sigma_f is None:
                excluded_ids.append(row_id)
                continue
            
            # Normalize
            d_sigma = (sigma - sigma_0) / sigma_0
            d_E = (E - E_0) / E_0
            d_sigma_f = (sigma_f - sigma_f_0) / sigma_f_0
            
            new_row = row.copy()
            new_row["delta_conductivity"] = d_sigma
            new_row["delta_youngs_modulus"] = d_E
            new_row["delta_fracture_strength"] = d_sigma_f
            normalized.append(new_row)
            
        except Exception as e:
            logger.warning(f"Error processing row {row_id}: {e}")
            excluded_ids.append(row_id)
            
    return normalized, excluded_ids

def one_hot_encode_defect_type(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    One-hot encodes the 'defect_type' column.
    Returns encoded data and list of new feature names.
    """
    if not data:
        return [], []
    
    # Collect all unique defect types
    types = set()
    for row in data:
        t = row.get("defect_type", "unknown")
        types.add(t)
    
    type_list = sorted(list(types))
    new_features = [f"defect_type_{t}" for t in type_list]
    
    encoded_data = []
    for row in data:
        new_row = row.copy()
        t = row.get("defect_type", "unknown")
        for feat in new_features:
            new_row[feat] = 1 if feat.endswith(f"_{t}") else 0
        encoded_data.append(new_row)
        
    return encoded_data, new_features

def compute_vif(features: List[List[float]]) -> List[float]:
    """
    Computes Variance Inflation Factor for a list of feature columns.
    Simple implementation for small datasets.
    """
    import numpy as np
    if not features or len(features) == 0:
        return []
    
    X = np.array(features).T # Shape: (n_samples, n_features)
    n_features = X.shape[1]
    vifs = []
    
    for i in range(n_features):
        y = X[:, i]
        X_other = np.delete(X, i, axis=1)
        
        # Fit linear model y ~ X_other
        try:
            # Add intercept
            X_other_with_intercept = np.column_stack((np.ones(X_other.shape[0]), X_other))
            coeffs, residuals, rank, s = np.linalg.lstsq(X_other_with_intercept, y, rcond=None)
            
            if len(residuals) > 0:
                ss_res = residuals[0]
            else:
                # If perfect fit or singular
                y_pred = X_other_with_intercept @ coeffs
                ss_res = np.sum((y - y_pred)**2)
            
            ss_tot = np.sum((y - np.mean(y))**2)
            
            if ss_tot == 0:
                r2 = 0
            else:
                r2 = 1 - (ss_res / ss_tot)
            
            if r2 >= 1.0:
                vifs.append(float('inf'))
            else:
                vifs.append(1.0 / (1.0 - r2))
        except Exception:
            vifs.append(float('inf'))
            
    return vifs

def handle_collinearity(data: List[Dict[str, Any]], feature_cols: List[str]) -> Tuple[List[Dict[str, Any]], List[str], Dict]:
    """
    Handles collinearity by removing features with high VIF.
    Returns cleaned data, remaining feature names, and log.
    """
    import numpy as np
    
    log = {
        "iterations": 0,
        "removed_features": [],
        "final_vifs": {},
        "status": "SUCCESS"
    }
    
    current_features = list(feature_cols)
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        log["iterations"] = iteration
        
        # Extract feature matrix
        matrix = []
        for row in data:
            row_vals = []
            for f in current_features:
                val = parse_float_safe(row.get(f), 0.0)
                row_vals.append(val)
            matrix.append(row_vals)
        
        if not matrix:
            break
            
        vifs = compute_vif(matrix)
        
        # Check if all VIFs <= 5
        max_vif = max(vifs) if vifs else 0
        if max_vif <= 5:
            log["status"] = "SUCCESS"
            break
        
        # Find feature with highest VIF
        max_vif_idx = vifs.index(max_vif)
        removed_feature = current_features[max_vif_idx]
        
        log["removed_features"].append(removed_feature)
        current_features.pop(max_vif_idx)
        
        if not current_features:
            log["status"] = "VIF_FAILURE"
            break
    
    log["final_vifs"] = {f: v for f, v in zip(current_features, vifs)}
    
    return data, current_features, log

def process_data() -> None:
    """
    Main processing pipeline for T018.
    1. Load pristine structures.
    2. Extract references.
    3. Load defect dataset.
    4. Normalize targets.
    5. Exclude missing references and log.
    6. One-hot encode.
    7. Save features, targets, and normalization log.
    """
    ensure_output_directories()
    project_root = get_project_root()
    
    # 1. Load Pristine Structures
    pristine_data = load_pristine_structures()
    if not pristine_data:
        logger.error("No pristine structures found. Cannot normalize.")
        # Write empty outputs as required
        save_to_csv(project_root / "data" / "processed" / "features.csv", [], [])
        save_to_csv(project_root / "data" / "processed" / "targets.csv", [], [])
        save_json_file(project_root / "data" / "state" / "normalization_log.json", {"excluded_ids": [], "count": 0})
        return
        
    # 2. Extract References
    refs = extract_pristine_references(pristine_data)
    logger.info(f"Extracted references: {refs}")
    
    # 3. Load Defect Dataset
    defect_data = load_defect_dataset()
    if not defect_data:
        logger.warning("Defect dataset is empty.")
        save_to_csv(project_root / "data" / "processed" / "features.csv", [], [])
        save_to_csv(project_root / "data" / "processed" / "targets.csv", [], [])
        save_json_file(project_root / "data" / "state" / "normalization_log.json", {"excluded_ids": [], "count": 0})
        return
    
    # 4. Normalize Targets
    normalized_data, excluded_ids = normalize_targets(defect_data, refs)
    
    # 5. Log Exclusions
    exclusion_log = {
        "excluded_ids": excluded_ids,
        "count": len(excluded_ids)
    }
    save_json_file(project_root / "data" / "state" / "normalization_log.json", exclusion_log)
    logger.info(f"Excluded {len(excluded_ids)} entries due to missing references.")
    
    if not normalized_data:
        logger.warning("No data left after normalization.")
        save_to_csv(project_root / "data" / "processed" / "features.csv", [], [])
        save_to_csv(project_root / "data" / "processed" / "targets.csv", [], [])
        return
        
    # 6. One-Hot Encode
    encoded_data, new_features = one_hot_encode_defect_type(normalized_data)
    
    # 7. Prepare Features and Targets
    # Features: defect_type (encoded), defect_density, etc.
    # Targets: delta_conductivity, delta_youngs_modulus, delta_fracture_strength
    
    target_cols = ["delta_conductivity", "delta_youngs_modulus", "delta_fracture_strength"]
    # Assuming defect_density and encoded defect types are features
    # We need to identify other feature columns dynamically or from config
    # For now, let's assume all numeric columns except targets and ID are features
    
    feature_cols = []
    for col in encoded_data[0].keys():
        if col.startswith("defect_type_"):
            feature_cols.append(col)
        elif col == "defect_density":
            feature_cols.append(col)
        elif col not in target_cols and col not in ["id", "entry_id", "conductivity", "youngs_modulus", "fracture_strength"]:
            # Check if numeric
            val = parse_float_safe(encoded_data[0].get(col))
            if val != 0.0 or col in ["defect_density"]: # Heuristic
                feature_cols.append(col)
    
    # Extract Features
    features_list = []
    for row in encoded_data:
        feat_row = {k: row[k] for k in feature_cols}
        features_list.append(feat_row)
        
    # Extract Targets
    targets_list = []
    for row in encoded_data:
        tgt_row = {k: row[k] for k in target_cols}
        # Add ID for traceability
        tgt_row["id"] = row.get("id", row.get("entry_id"))
        targets_list.append(tgt_row)
    
    # 8. Save Outputs
    save_to_csv(project_root / "data" / "processed" / "features.csv", features_list)
    save_to_csv(project_root / "data" / "processed" / "targets.csv", targets_list)
    
    logger.info("Data processing complete.")

def update_state_with_checksums() -> None:
    """Updates state files with checksums of processed data."""
    project_root = get_project_root()
    features_path = project_root / "data" / "processed" / "features.csv"
    targets_path = project_root / "data" / "processed" / "targets.csv"
    
    state = {}
    if features_path.exists():
        state["features_sha256"] = compute_sha256(features_path)
    if targets_path.exists():
        state["targets_sha256"] = compute_sha256(targets_path)
        
    if state:
        # Append to existing state or create new
        current_state = load_json_file(project_root / "data" / "state" / "data_source.json")
        current_state.update(state)
        save_json_file(project_root / "data" / "state" / "data_source.json", current_state)

def main():
    """Entry point for the script."""
    logger.info("Starting data processing (T018)...")
    process_data()
    update_state_with_checksums()
    logger.info("Data processing finished.")

if __name__ == "__main__":
    main()