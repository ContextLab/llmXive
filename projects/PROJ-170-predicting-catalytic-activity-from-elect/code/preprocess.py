import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.neighbors import NearestNeighbors

# Import project utilities
from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger
from utils.hashing import compute_file_hash

# Setup logging
logger = get_logger(__name__)

def load_raw_oc20_data() -> pd.DataFrame:
    """
    Load the raw OC20 dataset from the downloaded H5 file.
    """
    data_path = get_data_path()
    raw_file = data_path / "raw" / "oc20_sample.h5"
    
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}. Run download_data.py first.")
    
    logger.info(f"Loading raw OC20 data from {raw_file}")
    try:
        # Attempt to read HDF5. Depending on the writer, it might be a table or a group.
        # Using pandas.read_hdf which is robust for simple tables.
        df = pd.read_hdf(raw_file, key='df')
        logger.info(f"Loaded {len(df)} rows from {raw_file}")
        return df
    except Exception as e:
        logger.error(f"Failed to load HDF5 file: {e}")
        # Fallback if key is not 'df' or format is different, try iterating keys
        try:
            import tables
            with pd.HDFStore(raw_file) as store:
                keys = store.keys()
                if keys:
                    df = pd.read_hdf(raw_file, key=keys[0])
                    logger.info(f"Loaded {len(df)} rows using key {keys[0]}")
                    return df
                else:
                    raise ValueError("No keys found in HDF5 file")
        except Exception as e2:
            raise RuntimeError(f"Could not load data from {raw_file}: {e2}")

def generate_morgan_fingerprint(mol: Chem.Mol, radius: int = 2, nBits: int = 2048) -> np.ndarray:
    """
    Generate a Morgan fingerprint (ECFP) for a molecule.
    Returns a numpy array of bits.
    """
    if mol is None:
        return np.zeros(nBits, dtype=int)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nBits)
    arr = np.zeros((nBits,), dtype=int)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def align_entries(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Align entries based on composition and surface_facet.
    Returns aligned dataframe and list of exclusions.
    """
    exclusions = []
    
    # Filter out rows missing critical alignment keys
    if 'composition' not in df.columns or 'surface_facet' not in df.columns:
        raise ValueError("Missing required columns 'composition' or 'surface_facet' for alignment.")
    
    mask_valid = df['composition'].notna() & df['surface_facet'].notna()
    excluded_count = (~mask_valid).sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows missing composition or surface_facet")
        exclusions.extend([
            {"row_idx": i, "reason": "missing_key"} 
            for i in df.index[~mask_valid]
        ])
    
    aligned_df = df[mask_valid].reset_index(drop=True)
    return aligned_df, exclusions

def save_exclusion_log(exclusions: List[Dict[str, Any]], log_path: Optional[Path] = None):
    """
    Save exclusion log to JSON.
    """
    if log_path is None:
        output_path = get_output_path()
        log_path = output_path / "exclusion_log.json"
    
    with open(log_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Saved exclusion log to {log_path}")

def retrieve_target_variable(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retrieve target variable 'energy_change'.
    Log and exclude rows with missing target.
    """
    if 'energy_change' not in df.columns:
        raise ValueError("Target column 'energy_change' not found in dataset.")
    
    mask_nan = df['energy_change'].isna()
    if mask_nan.any():
        logger.warning(f"Excluding {mask_nan.sum()} rows with missing 'energy_change'")
        df = df[~mask_nan].reset_index(drop=True)
    
    return df

def compute_alignment_success_rate(original_count: int, final_count: int) -> float:
    """
    Compute the success rate of alignment.
    """
    if original_count == 0:
        return 0.0
    return final_count / original_count

def save_alignment_metrics(metrics: Dict[str, Any], path: Optional[Path] = None):
    """
    Save alignment metrics to JSON.
    """
    if path is None:
        output_path = get_output_path()
        path = output_path / "alignment_metrics.json"
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved alignment metrics to {path}")

def impute_descriptors_knn(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """
    Impute missing descriptors using k-nearest-neighbors based on Morgan fingerprints.
    Excludes rows where < k neighbors exist.
    """
    # Identify descriptor columns (exclude target and identifiers)
    exclude_cols = {'energy_change', 'composition', 'surface_facet', 'id'}
    desc_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.float64, np.float32, np.int64, np.int32]]
    
    if not desc_cols:
        logger.warning("No numeric descriptor columns found for imputation.")
        return df

    # Generate fingerprints for all rows
    logger.info("Generating Morgan fingerprints for KNN imputation...")
    fingerprints = []
    valid_indices = []
    
    # Assuming 'composition' is a string representation of the formula
    # We need to parse it to generate a molecule. 
    # Note: OC20 'composition' might be a string like "H2O" or a list. 
    # We assume string format for RDKit parsing.
    
    for idx, row in df.iterrows():
        comp_str = str(row.get('composition', ''))
        if not comp_str or comp_str == 'nan':
            continue
        
        try:
            # Simple heuristic: if it looks like a formula, try to build a mol
            # RDKit might fail on complex inorganic formulas without explicit structure.
            # However, for the sake of this pipeline, we assume the 'composition'
            # is sufficient for a rough fingerprint or we skip if invalid.
            # A more robust approach would require a structure file, but we are limited to columns.
            # We will try to parse as SMILES if possible, or just skip if it's just a formula string.
            # Since OC20 'composition' is often just a formula string (e.g. "Fe2O3"), 
            # RDKit's MolFromSmiles won't work directly on formulas.
            # We will use a placeholder approach: if we can't make a mol, we skip imputation for that row 
            # or use a random hash? No, that's bad.
            # Alternative: Use the composition string as a categorical feature for distance?
            # The task says "Structure-based KNN (Morgan fingerprints)". 
            # This implies we MUST have a molecule object. 
            # If the dataset only has 'composition' string, we cannot generate a real Morgan fingerprint 
            # without a 3D structure or a generated 2D structure.
            # Given the constraints, we will attempt to generate a mol from the composition string 
            # by assuming it's a valid SMILES (unlikely) or skip.
            # BETTER: If we cannot generate a fingerprint, we treat that row as having no neighbors 
            # and exclude it from the imputation process (flag it).
            
            mol = Chem.MolFromSmiles(comp_str)
            if mol is None:
                # Try to interpret as a formula? RDKit doesn't support formula->mol directly without rules.
                # We will skip this row for KNN basis, effectively excluding it from imputation 
                # if it relies on structure.
                continue
            
            fp = generate_morgan_fingerprint(mol)
            fingerprints.append(fp)
            valid_indices.append(idx)
        except Exception:
            continue
    
    if len(fingerprints) == 0:
        logger.warning("Could not generate any valid fingerprints for KNN. Skipping imputation.")
        return df
    
    fingerprints = np.array(fingerprints)
    valid_df = df.loc[valid_indices].reset_index(drop=True)
    
    # Identify rows with missing values in descriptors
    missing_mask = valid_df[desc_cols].isna().any(axis=1)
    rows_to_impute = valid_df[missing_mask]
    rows_to_keep = valid_df[~missing_mask]
    
    if len(rows_to_impute) == 0:
        logger.info("No missing values to impute.")
        return df
    
    logger.info(f"Imputing {len(rows_to_impute)} rows using KNN (k={k})...")
    
    # Fit KNN on the fingerprint space of rows that have valid fingerprints
    # We need to impute the descriptor values for the 'rows_to_impute' based on neighbors in 'fingerprints'
    # But wait, the KNN should be based on the fingerprints of the rows we are imputing?
    # Yes. We need fingerprints for the rows we want to impute.
    # The loop above skipped rows where mol generation failed.
    # We need to ensure we have fingerprints for the rows we are trying to impute.
    
    # Re-do fingerprint generation specifically for the subset we need to impute
    # and the subset we use as reference (the whole valid set).
    
    # Reference set: all rows with valid fingerprints
    ref_fps = fingerprints
    ref_indices = valid_indices
    
    # Query set: rows_to_impute
    query_fps = []
    query_indices = []
    for idx in rows_to_impute.index:
        row = df.loc[idx]
        comp_str = str(row.get('composition', ''))
        try:
            mol = Chem.MolFromSmiles(comp_str)
            if mol:
                fp = generate_morgan_fingerprint(mol)
                query_fps.append(fp)
                query_indices.append(idx)
        except:
            continue
    
    if len(query_fps) == 0:
        logger.warning("No valid fingerprints for rows to impute. Skipping.")
        return df
    
    query_fps = np.array(query_fps)
    
    # Fit KNN
    nbrs = NearestNeighbors(n_neighbors=k, metric='euclidean')
    nbrs.fit(ref_fps)
    
    # Find neighbors
    distances, indices = nbrs.kneighbors(query_fps)
    
    # Impute
    imputed_df = df.copy()
    excluded_indices = []
    
    for i, q_idx in enumerate(query_indices):
        if distances[i, -1] == np.inf: # Should not happen if fit is correct
            excluded_indices.append(q_idx)
            continue
        
        neighbor_indices = ref_indices[indices[i]]
        neighbor_values = valid_df.loc[neighbor_indices, desc_cols]
        
        # Check if we have enough neighbors (k)
        if len(neighbor_values) < k:
            excluded_indices.append(q_idx)
            continue
        
        # Mean imputation
        mean_vals = neighbor_values.mean(axis=0)
        imputed_df.loc[q_idx, desc_cols] = mean_vals.values
    
    if excluded_indices:
        logger.warning(f"Excluding {len(excluded_indices)} rows due to insufficient neighbors for imputation.")
        # Mark these rows for exclusion later or drop them
        # For now, we return the imputed df, but the caller should handle these exclusions
        # We can add a flag column
        imputed_df['imputation_failed'] = False
        imputed_df.loc[excluded_indices, 'imputation_failed'] = True
    
    return imputed_df

def scale_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Scale all numeric features to zero mean and unit variance.
    Excludes target and identifier columns.
    Returns scaled dataframe and the scaler parameters for reproducibility.
    """
    exclude_cols = {'energy_change', 'composition', 'surface_facet', 'id', 'imputation_failed'}
    
    # Identify numeric columns to scale
    numeric_cols = []
    for col in df.columns:
        if col in exclude_cols:
            continue
        if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
            numeric_cols.append(col)
    
    if not numeric_cols:
        logger.warning("No numeric columns found to scale.")
        return df, {}
    
    logger.info(f"Scaling {len(numeric_cols)} numeric features: {numeric_cols[:5]}...")
    
    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(df[numeric_cols])
    
    df_scaled = df.copy()
    df_scaled[numeric_cols] = scaled_values
    
    # Save scaler params (mean and std) for potential inverse transform or logging
    scaler_params = {
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "var": scaler.var_.tolist(),
        "features": numeric_cols
    }
    
    logger.info("Feature scaling completed successfully.")
    return df_scaled, scaler_params

def main():
    """
    Main entry point for preprocessing pipeline.
    Executes: Load -> Align -> Target Retrieval -> Imputation -> Scaling.
    """
    setup_logging()
    logger.info("Starting Preprocessing Pipeline (T019: Scaling)")
    
    try:
        # 1. Load Raw Data
        df = load_raw_oc20_data()
        original_count = len(df)
        
        # 2. Align Entries
        df, exclusions = align_entries(df)
        save_exclusion_log(exclusions)
        
        # 3. Retrieve Target
        df = retrieve_target_variable(df)
        
        # 4. Impute Descriptors
        df = impute_descriptors_knn(df, k=5)
        
        # Handle rows that failed imputation
        if 'imputation_failed' in df.columns:
            failed_count = df['imputation_failed'].sum()
            if failed_count > 0:
                logger.warning(f"Excluding {failed_count} rows due to imputation failure.")
                df = df[~df['imputation_failed']].drop(columns=['imputation_failed'])
            else:
                df = df.drop(columns=['imputation_failed'])
        
        # 5. Scale Features (T019)
        df_scaled, scaler_params = scale_features(df)
        
        # Save scaler parameters
        output_path = get_output_path()
        scaler_path = output_path / "scaler_params.json"
        with open(scaler_path, 'w') as f:
            json.dump(scaler_params, f, indent=2)
        logger.info(f"Saved scaler parameters to {scaler_path}")
        
        # Compute and save alignment metrics
        metrics = {
            "original_count": original_count,
            "final_count": len(df_scaled),
            "alignment_success_rate": compute_alignment_success_rate(original_count, len(df_scaled))
        }
        save_alignment_metrics(metrics)
        
        logger.info(f"Preprocessing complete. Final dataset size: {len(df_scaled)}")
        logger.info("Scaling step (T019) successful.")
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()