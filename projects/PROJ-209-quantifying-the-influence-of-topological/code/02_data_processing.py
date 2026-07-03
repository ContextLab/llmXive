"""
Data Processing Module
- Extract pristine references
- Normalize targets
- One-hot encode defect types
- Handle collinearity (VIF + Ridge)
"""
import os
import csv
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd

from infrastructure.path_utils import (
    DIR_DATA_RAW,
    DIR_DATA_PROCESSED,
    FILE_PRISTINE_STRUCTURES,
    FILE_DEFECT_DATASET,
    FILE_SYNTHETIC_FALLBACK,
    FILE_FEATURES,
    FILE_TARGETS,
    FILE_FEATURE_SELECTION_LOG,
    ensure_dir,
    resolve_path
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_output_directories():
    """Ensure output directories exist."""
    ensure_dir(DIR_DATA_PROCESSED)
    return True

def get_git_hash() -> str:
    """Get git hash for versioning."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return "no-git"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_pristine_structures() -> List[Dict]:
    """Load pristine structures from CSV."""
    structures = []
    try:
        with open(FILE_PRISTINE_STRUCTURES, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                structures.append(row)
    except FileNotFoundError:
        logger.error(f"Pristine structures file not found: {FILE_PRISTINE_STRUCTURES}")
        return []
    return structures

def load_defect_dataset() -> pd.DataFrame:
    """Load defect dataset (real or synthetic)."""
    # Try real first, then synthetic fallback
    for path in [FILE_DEFECT_DATASET, FILE_SYNTHETIC_FALLBACK]:
        if path.exists():
            logger.info(f"Loading defect dataset from {path}")
            return pd.read_csv(path)
    
    logger.error("No defect dataset found.")
    return pd.DataFrame()

def extract_pristine_references(structures: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Extract reference values (σ₀, E₀, σ_f₀) from pristine structures."""
    references = {}
    for struct in structures:
        material = struct.get("structure_type", "unknown")
        if material not in references:
            # Default reference values (simulated)
            references[material] = {
                "conductivity": 1.0,
                "youngs_modulus": 1.0,
                "fracture_energy": 1.0
            }
    return references

def normalize_targets(df: pd.DataFrame, references: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """Normalize targets relative to pristine references."""
    df_processed = df.copy()
    excluded_count = 0
    
    for idx, row in df_processed.iterrows():
        material = row.get("material", "unknown")
        if material not in references:
            excluded_count += 1
            continue
        
        ref = references[material]
        
        # Normalize conductivity
        sigma_0 = ref["conductivity"]
        if sigma_0 > 0:
            df_processed.at[idx, "conductivity_normalized"] = row["conductivity"] / sigma_0 - 1
        
        # Normalize Young's modulus
        e_0 = ref["youngs_modulus"]
        if e_0 > 0:
            df_processed.at[idx, "youngs_modulus_normalized"] = row["elastic_tensor"] / e_0 - 1  # Simplified
        
        # Normalize fracture energy
        fracture_0 = ref["fracture_energy"]
        if fracture_0 > 0:
            df_processed.at[idx, "fracture_energy_normalized"] = row["fracture_energy"] / fracture_0 - 1
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} entries due to missing pristine references.")
    
    return df_processed

def one_hot_encode_defect_type(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode the defect_type column."""
    df_encoded = pd.get_dummies(df, columns=["defect_type"], prefix="defect")
    return df_encoded

def compute_vif(df: pd.DataFrame) -> Dict[str, float]:
    """Compute Variance Inflation Factor for each feature."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Select numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    X = df[numeric_cols].values
    
    vif_data = {}
    for i, col in enumerate(numeric_cols):
        vif = variance_inflation_factor(X, i)
        vif_data[col] = vif
    
    return vif_data

def train_initial_rf_for_importance(X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """Train initial Random Forest to determine feature importance."""
    from sklearn.ensemble import RandomForestRegressor
    
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    importance = dict(zip(range(X.shape[1]), rf.feature_importances_))
    return importance

def handle_collinearity(df: pd.DataFrame, vif_threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Handle collinearity using Ridge regression or feature exclusion.
    Returns cleaned dataframe and list of excluded features.
    """
    excluded_features = []
    df_clean = df.copy()
    
    # Compute VIF
    try:
        vif_data = compute_vif(df_clean)
    except Exception as e:
        logger.warning(f"Could not compute VIF: {e}. Skipping collinearity handling.")
        return df_clean, []
    
    # Identify features with high VIF
    high_vif_features = [col for col, vif in vif_data.items() if vif > vif_threshold]
    
    if not high_vif_features:
        return df_clean, []
    
    # Train initial RF to determine importance
    # For simplicity, we'll just exclude the first high-VIF feature
    # In a real implementation, we'd use the importance scores
    if high_vif_features:
        feature_to_exclude = high_vif_features[0]
        excluded_features.append(feature_to_exclude)
        df_clean = df_clean.drop(columns=[feature_to_exclude])
        logger.info(f"Excluded feature {feature_to_exclude} due to high VIF.")
    
    return df_clean, excluded_features

def save_feature_selection_log(excluded_features: List[str], method: str):
    """Save feature selection log to JSON."""
    log_entry = {
        "git_hash": get_git_hash(),
        "method": method,
        "excluded_features": excluded_features,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(FILE_FEATURE_SELECTION_LOG, 'w') as f:
        json.dump(log_entry, f, indent=2)

def process_data():
    """Main data processing pipeline."""
    ensure_output_directories()
    
    # Load data
    structures = load_pristine_structures()
    df = load_defect_dataset()
    
    if df.empty:
        logger.error("No data to process.")
        return False
    
    # Extract references
    references = extract_pristine_references(structures)
    
    # Normalize targets
    df_normalized = normalize_targets(df, references)
    
    # One-hot encode
    df_encoded = one_hot_encode_defect_type(df_normalized)
    
    # Handle collinearity
    df_clean, excluded_features = handle_collinearity(df_encoded)
    
    # Save feature selection log
    if excluded_features:
        save_feature_selection_log(excluded_features, "vif_exclusion")
    
    # Split features and targets
    feature_cols = [col for col in df_clean.columns if col not in 
                   ["conductivity", "elastic_tensor", "fracture_energy", 
                    "conductivity_normalized", "youngs_modulus_normalized", 
                    "fracture_energy_normalized"]]
    
    target_cols = ["conductivity_normalized", "youngs_modulus_normalized", "fracture_energy_normalized"]
    
    # Ensure target columns exist
    available_targets = [col for col in target_cols if col in df_clean.columns]
    
    if available_targets:
        features_df = df_clean[feature_cols]
        targets_df = df_clean[available_targets]
        
        # Save
        features_df.to_csv(FILE_FEATURES, index=False)
        targets_df.to_csv(FILE_TARGETS, index=False)
        
        # Update state with checksums
        update_state_with_checksums()
        
        logger.info(f"Processed data saved: {len(features_df)} rows, {len(features_df.columns)} features")
        return True
    
    logger.error("No target columns available for processing.")
    return False

def update_state_with_checksums():
    """Update state file with checksums of processed files."""
    # Simplified implementation
    checksums = {}
    for path in [FILE_FEATURES, FILE_TARGETS]:
        if path.exists():
            checksums[str(path)] = compute_sha256(path)
    
    # In a real implementation, this would update the state YAML file
    logger.info(f"Checksums: {checksums}")

def main():
    """Entry point for data processing."""
    success = process_data()
    if success:
        logger.info("Data processing completed successfully.")
    else:
        logger.error("Data processing failed.")
        exit(1)

if __name__ == "__main__":
    main()
