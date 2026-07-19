"""
Data Processing Module for PROJ-209: Quantifying the Influence of Topological Defects.

This module handles:
1. Extraction of scalar reference values from pristine structures.
2. Normalization of target properties (conductivity, Young's modulus, fracture strength).
3. Feature engineering (one-hot encoding).
4. Collinearity handling (VIF calculation).
5. Data output generation (features.csv, targets.csv).
"""
import os
import csv
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set

import numpy as np
import pandas as pd
from scipy import stats

# Import shared utilities from 01_data_acquisition if needed, or define locally
# Based on API surface, we assume standard imports and define helpers here if not in 01_data_acquisition
# However, the prompt says "import as: from 01_data_acquisition import ...". 
# We will use the provided API surface names.

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parents[1]

def ensure_output_directories():
    """Creates necessary output directories if they do not exist."""
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
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json_file(file_path: Path) -> Dict:
    """Loads a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: Dict):
    """Saves data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_pristine_structures() -> pd.DataFrame:
    """
    Loads pristine structures from data/raw/pristine_structures.csv.
    Expects columns: material_id, conductivity, youngs_modulus, fracture_strength
    """
    path = get_project_root() / "data" / "raw" / "pristine_structures.csv"
    if not path.exists():
        raise FileNotFoundError(f"Pristine structures file not found: {path}")
    
    df = pd.read_csv(path)
    # Normalize column names to ensure consistency
    df.columns = df.columns.str.strip().str.lower()
    return df

def load_defect_dataset() -> pd.DataFrame:
    """
    Loads the defect dataset.
    Tries real dataset first, then synthetic if real is missing.
    """
    real_path = get_project_root() / "data" / "raw" / "defect_dataset_2022.csv"
    synth_path = get_project_root() / "data" / "raw" / "synthetic_train.csv"
    
    if real_path.exists():
        logger.info("Loading real defect dataset.")
        return pd.read_csv(real_path)
    elif synth_path.exists():
        logger.info("Real dataset missing, loading synthetic training data.")
        return pd.read_csv(synth_path)
    else:
        raise FileNotFoundError("Neither real nor synthetic defect dataset found.")

def extract_pristine_references(pristine_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Extracts scalar reference values (σ₀, E₀, σ_f₀) per material_id.
    Returns a dict: { material_id: { 'conductivity': val, 'youngs_modulus': val, 'fracture_strength': val } }
    """
    references = {}
    required_cols = ['material_id', 'conductivity', 'youngs_modulus', 'fracture_strength']
    
    # Ensure columns exist
    missing_cols = [c for c in required_cols if c not in pristine_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in pristine structures: {missing_cols}")

    for _, row in pristine_df.iterrows():
        mid = str(row['material_id']).strip()
        if not mid:
            continue
        
        # Check for missing reference values
        cond = row['conductivity']
        youngs = row['youngs_modulus']
        fracture = row['fracture_strength']

        # Handle potential NaN or None
        if pd.isna(cond) or pd.isna(youngs) or pd.isna(fracture):
            logger.warning(f"Skipping material {mid} due to missing reference values.")
            continue

        references[mid] = {
            'conductivity': float(cond),
            'youngs_modulus': float(youngs),
            'fracture_strength': float(fracture)
        }
    return references

def normalize_targets(defect_df: pd.DataFrame, pristine_refs: Dict[str, Dict[str, float]]) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Computes relative changes (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀).
    Returns:
      - features_df: Input features (defect properties)
      - targets_df: Normalized target values
      - excluded_ids: List of IDs excluded due to missing pristine references
    """
    excluded_ids = []
    valid_indices = []
    
    # Expected target columns in defect dataset
    target_cols = ['conductivity', 'youngs_modulus', 'fracture_strength']
    # Feature columns (everything else that isn't an ID or target)
    # We assume 'material_id' and 'defect_type' and 'defect_density' are present
    
    for idx, row in defect_df.iterrows():
        mid = str(row.get('material_id', '')).strip()
        
        if mid not in pristine_refs:
            excluded_ids.append(mid)
            continue
        
        ref = pristine_refs[mid]
        valid_indices.append(idx)

    if not valid_indices:
        raise ValueError("No valid entries found for normalization after excluding missing references.")

    features_list = []
    targets_list = []

    for idx in valid_indices:
        row = defect_df.iloc[idx]
        mid = str(row.get('material_id', '')).strip()
        ref = pristine_refs[mid]
        
        # Extract raw values
        raw_cond = row['conductivity']
        raw_youngs = row['youngs_modulus']
        raw_fracture = row['fracture_strength']
        
        # Calculate relative change: (raw - ref) / ref
        # If raw is NaN, result is NaN
        norm_cond = (raw_cond - ref['conductivity']) / ref['conductivity'] if pd.notna(raw_cond) else np.nan
        norm_youngs = (raw_youngs - ref['youngs_modulus']) / ref['youngs_modulus'] if pd.notna(raw_youngs) else np.nan
        norm_fracture = (raw_fracture - ref['fracture_strength']) / ref['fracture_strength'] if pd.notna(raw_fracture) else np.nan
        
        # Build feature row (excluding targets and material_id)
        feature_row = {}
        for col in defect_df.columns:
            if col not in target_cols and col != 'material_id':
                feature_row[col] = row[col]
        
        # Add normalized targets
        feature_row['norm_conductivity'] = norm_cond
        feature_row['norm_youngs_modulus'] = norm_youngs
        feature_row['norm_fracture_strength'] = norm_fracture
        feature_row['material_id'] = mid # Keep for traceability if needed, though targets will be separate
        
        features_list.append(feature_row)
        targets_list.append({
            'material_id': mid,
            'norm_conductivity': norm_cond,
            'norm_youngs_modulus': norm_youngs,
            'norm_fracture_strength': norm_fracture
        })

    features_df = pd.DataFrame(features_list)
    targets_df = pd.DataFrame(targets_list)
    
    return features_df, targets_df, excluded_ids

def one_hot_encode_defect_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encodes the 'defect_type' column if it exists.
    """
    if 'defect_type' not in df.columns:
        return df
    
    dummies = pd.get_dummies(df['defect_type'], prefix='defect_type')
    df = pd.concat([df.drop('defect_type', axis=1), dummies], axis=1)
    return df

def compute_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Computes Variance Inflation Factor (VIF) for a list of features.
    """
    vif_data = {}
    X = df[features].dropna() # Drop rows with NaNs for VIF calculation
    if X.empty:
        return {f: np.inf for f in features}
    
    for i, feature in enumerate(features):
        y = X[feature]
        X_other = X.drop(columns=[feature])
        if X_other.shape[1] == 0:
            vif_data[feature] = 1.0
            continue
        
        try:
            r2 = stats.pearsonr(y, X_other.mean(axis=1))[0]**2 # Simplified for single correlation check? No, need R2.
            # Correct R2 calculation:
            model = stats.linregress(X_other.iloc[:, 0], y) # This is wrong for multiple
            # Use OLS from statsmodels if available, otherwise manual
            # Manual OLS: (X'X)^-1 X'y
            # For simplicity and dependency minimization, let's use a simple loop or assume statsmodels
            # But standard library only? Let's try to use numpy
            X_mat = X_other.values
            X_mat = np.column_stack([np.ones(X_mat.shape[1]), X_mat]) # Add intercept? No, VIF is about correlation with OTHERS
            # Actually, VIF for feature j is 1 / (1 - R_j^2) where R_j^2 is from regressing j on all others.
            # We need to handle multiple features properly.
            
            # Fallback to a simple approximation if statsmodels not available, but let's assume we can use numpy.linalg
            # We need to regress feature j on all other features.
            X_j = X[feature].values
            X_others = X.drop(columns=[feature]).values
            
            # Add intercept column for regression
            X_others_int = np.c_[np.ones(X_others.shape[0]), X_others]
            
            try:
                coeffs, _, _, _ = np.linalg.lstsq(X_others_int, X_j, rcond=None)
                y_pred = X_others_int @ coeffs
                ss_res = np.sum((X_j - y_pred) ** 2)
                ss_tot = np.sum((X_j - np.mean(X_j)) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
                r2 = max(0.0, min(1.0, r2)) # Clamp
                vif = 1.0 / (1.0 - r2) if r2 < 1.0 else np.inf
            except np.linalg.LinAlgError:
                vif = np.inf
            
            vif_data[feature] = vif
        except Exception as e:
            logger.warning(f"Could not compute VIF for {feature}: {e}")
            vif_data[feature] = np.inf
    
    return vif_data

def handle_collinearity(df: pd.DataFrame, features: List[str], vif_threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Iteratively removes features with VIF > threshold until all are below threshold or max iterations reached.
    """
    current_features = list(features)
    iteration = 0
    max_iterations = 10
    log = []
    
    while iteration < max_iterations:
        vif_scores = compute_vif(df, current_features)
        max_vif = max(vif_scores.values())
        
        if max_vif <= vif_threshold:
            break
        
        # Find feature with highest VIF
        worst_feature = max(vif_scores, key=vif_scores.get)
        log.append({
            "iteration": iteration,
            "removed_feature": worst_feature,
            "vif_score": vif_scores[worst_feature],
            "remaining_features": current_features
        })
        
        current_features.remove(worst_feature)
        iteration += 1
    
    if iteration == max_iterations and max(vif_scores.values()) > vif_threshold:
        logger.warning("VIF_FAILURE: Could not reduce VIF below threshold within max iterations.")
    
    return df[current_features], current_features, log

def process_data():
    """
    Main processing pipeline for T018.
    1. Load pristine structures.
    2. Load defect dataset.
    3. Extract references.
    4. Normalize targets.
    5. Handle collinearity (VIF).
    6. Save outputs.
    """
    ensure_output_directories()
    project_root = get_project_root()
    
    logger.info("Starting data processing (T018)...")
    
    # 1. Load Data
    try:
        pristine_df = load_pristine_structures()
    except FileNotFoundError as e:
        logger.error(f"Failed to load pristine structures: {e}")
        raise
    
    try:
        defect_df = load_defect_dataset()
    except FileNotFoundError as e:
        logger.error(f"Failed to load defect dataset: {e}")
        raise
    
    # 2. Extract References
    pristine_refs = extract_pristine_references(pristine_df)
    logger.info(f"Extracted {len(pristine_refs)} pristine references.")
    
    # 3. Normalize Targets
    features_df, targets_df, excluded_ids = normalize_targets(defect_df, pristine_refs)
    logger.info(f"Normalized {len(features_df)} entries. Excluded {len(excluded_ids)} entries.")
    
    # 4. One-Hot Encode
    features_df = one_hot_encode_defect_type(features_df)
    
    # 5. Select Features for VIF (Exclude targets and material_id)
    # Identify numeric features for VIF
    numeric_features = features_df.select_dtypes(include=[np.number]).columns.tolist()
    # Remove target columns from feature list
    target_cols = ['norm_conductivity', 'norm_youngs_modulus', 'norm_fracture_strength']
    feature_cols_for_vif = [c for c in numeric_features if c not in target_cols]
    
    # 6. Handle Collinearity
    final_features_df, final_feature_list, vif_log = handle_collinearity(features_df, feature_cols_for_vif)
    
    # Prepare final feature set (include non-numeric if needed, but VIF is for numeric)
    # For simplicity, we output the dataframe with all features but ensure numeric ones are clean
    # The task asks for features.csv and targets.csv
    
    # 7. Save Outputs
    features_path = project_root / "data" / "processed" / "features.csv"
    targets_path = project_root / "data" / "processed" / "targets.csv"
    norm_log_path = project_root / "data" / "state" / "normalization_log.json"
    vif_log_path = project_root / "data" / "processed" / "feature_selection_log.json"
    
    final_features_df.to_csv(features_path, index=False)
    targets_df.to_csv(targets_path, index=False)
    
    normalization_log = {
        "total_entries": len(defect_df),
        "processed_entries": len(features_df),
        "excluded_count": len(excluded_ids),
        "excluded_ids": excluded_ids,
        "vif_failure": iteration == max_iterations and max(vif_scores.values()) > vif_threshold if 'vif_scores' in locals() else False,
        "vif_log": vif_log
    }
    
    save_json_file(norm_log_path, normalization_log)
    save_json_file(vif_log_path, vif_log)
    
    logger.info(f"Saved features to {features_path}")
    logger.info(f"Saved targets to {targets_path}")
    logger.info(f"Saved normalization log to {norm_log_path}")
    
    return features_path, targets_path, norm_log_path

def update_state_with_checksums():
    """Updates state files with checksums of processed data."""
    # This is T019, but we can call it here if needed, or leave it for the main entry point
    pass

def main():
    """Entry point for the script."""
    try:
        process_data()
        logger.info("T018 completed successfully.")
    except Exception as e:
        logger.error(f"T018 failed: {e}")
        raise

if __name__ == "__main__":
    main()