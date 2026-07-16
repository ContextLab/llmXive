import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler

from config import get_project_root, get_data_path, get_output_path
from logging_config import get_logger
from utils.validation import validate_schema

# Initialize logger
logger = get_logger(__name__)

def load_raw_oc20_data() -> pd.DataFrame:
    """
    Load the raw OC20 sample from the downloaded H5 file.
    """
    data_path = get_data_path("raw/oc20_sample.h5")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Raw data file not found: {data_path}")
    
    logger.info(f"Loading raw data from {data_path}")
    df = pd.read_hdf(data_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def generate_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate a Morgan fingerprint (ECFP) for a given SMILES string.
    Returns a numpy array of bits (0 or 1).
    """
    if not isinstance(smiles, str) or not smiles:
        return np.zeros(n_bits, dtype=int)
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(n_bits, dtype=int)
        
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros((n_bits,), dtype=int)
        AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.warning(f"Failed to generate fingerprint for SMILES '{smiles}': {e}")
        return np.zeros(n_bits, dtype=int)

def align_entries(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Align OC20 entries using exact string matching on 'composition' and 'surface_facet'.
    
    CRITICAL (FR-002): Explicitly exclude entries where 'synthesis_condition' 
    cannot be uniquely identified. In this single-source pivot (OC20 only), 
    synthesis conditions are not uniquely identified per entry in a way that 
    prevents circular validation. Therefore, ALL entries are excluded from the 
    final training set based on this rule, but we log them for transparency.
    
    Returns:
        Tuple of (aligned_df, exclusion_log)
    """
    logger.info("Starting entry alignment...")
    
    # Check for required columns
    required_cols = ['composition', 'surface_facet', 'synthesis_condition']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for alignment: {missing_cols}")

    # 1. Exact string matching on composition and surface_facet
    # We assume the input df already has these columns populated from OC20.
    # The alignment logic here is primarily to ensure we have valid pairs
    # and to handle the exclusion logic mandated by FR-002.
    
    # For this specific task (T014), the alignment is trivial because we are
    # working with a single dataset (OC20) that was already downloaded.
    # The "alignment" is effectively validating that the entries exist and
    # then applying the exclusion rule.
    
    # Filter out rows where composition or surface_facet are missing/NaN
    valid_mask = df['composition'].notna() & df['surface_facet'].notna()
    valid_df = df[valid_mask].copy()
    excluded_align = df[~valid_mask].copy()
    
    if not excluded_align.empty:
        logger.warning(f"Excluded {len(excluded_align)} rows due to missing composition/facet.")

    # 2. FR-002 Exclusion Logic:
    # "explicitly exclude entries where 'synthesis_condition' cannot be uniquely identified"
    # In the context of OC20 (single source), the synthesis condition is often a complex
    # string or a set of parameters that are not uniquely identified in a way that
    # allows for non-circular validation against the target variable (energy_change)
    # without external metadata.
    #
    # Per the task description: "which applies to all entries in this single-source pivot"
    # Therefore, we exclude ALL entries from the final aligned dataset for training,
    # but we must log them.
    
    exclusion_log = []
    final_aligned_rows = []
    
    for idx, row in valid_df.iterrows():
        # Check if synthesis_condition is uniquely identified
        # Since we are in a single-source pivot, we assume it is NOT uniquely identified
        # for the purpose of this specific research constraint (FR-002).
        # We log every entry as excluded.
        
        exclusion_reason = (
            f"Entry excluded per FR-002: 'synthesis_condition' not uniquely identified "
            f"in single-source OC20 pivot. Composition: {row['composition']}, "
            f"Facet: {row['surface_facet']}"
        )
        
        exclusion_log.append({
            "index": idx,
            "composition": row['composition'],
            "surface_facet": row['surface_facet'],
            "reason": exclusion_reason
        })
        
        # We do NOT add to final_aligned_rows because they are excluded
    
    # The resulting aligned_df is effectively empty for training purposes
    # but we return the structure to maintain the pipeline flow if needed
    # or to show the attempted alignment.
    # However, to prevent downstream errors, we return an empty dataframe
    # with the expected schema if we are strictly following the exclusion.
    # But wait, T015 says "Retrieve target variable". T017 says "Impute".
    # If we exclude ALL, the dataset is empty.
    #
    # Re-reading T014: "explicitly exclude entries... to prevent circular validation"
    # This implies the dataset for *training* should not contain these.
    # If all are excluded, the dataset is empty.
    #
    # Let's assume the "alignment" step produces the set of candidates,
    # and the exclusion step filters them. If all are filtered, we have 0 rows.
    #
    # To ensure the pipeline doesn't crash immediately on empty data,
    # we return the empty dataframe but log the exclusions.
    # If the user intended to keep some, the logic for "uniquely identified"
    # would need to be more granular. Based on "applies to all entries",
    # we exclude all.
    
    if not valid_df.empty:
        # Create an empty dataframe with the expected columns to avoid schema errors later
        # We keep the columns that would be present if not excluded, but drop the rows.
        final_aligned_df = pd.DataFrame(columns=valid_df.columns)
    else:
        final_aligned_df = pd.DataFrame(columns=valid_df.columns) if 'valid_df' in locals() else pd.DataFrame()

    logger.info(f"Alignment complete. {len(valid_df)} candidates, {len(exclusion_log)} excluded by FR-002.")
    return final_aligned_df, exclusion_log

def save_exclusion_log(exclusion_log: List[Dict[str, Any]], output_dir: Optional[str] = None) -> str:
    """
    Save the exclusion log to a JSON file.
    """
    if output_dir is None:
        output_dir = get_output_path("")
    
    output_path = Path(output_dir) / "exclusion_log.json"
    
    with open(output_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    logger.info(f"Saved exclusion log to {output_path}")
    return str(output_path)

def retrieve_target_variable(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retrieve the target variable 'energy_change' from the dataframe.
    Log any missing target values.
    """
    if 'energy_change' not in df.columns:
        raise ValueError("Column 'energy_change' not found in dataframe.")
    
    missing_targets = df['energy_change'].isna().sum()
    if missing_targets > 0:
        logger.warning(f"Found {missing_targets} missing target values (energy_change).")
        # Drop rows with missing targets if any
        df = df.dropna(subset=['energy_change'])
    
    return df

def compute_alignment_success_rate(total_entries: int, matched_entries: int) -> float:
    """
    Compute the alignment success rate.
    """
    if total_entries == 0:
        return 0.0
    return matched_entries / total_entries

def save_alignment_metrics(metrics: Dict[str, Any], output_dir: Optional[str] = None) -> str:
    """
    Save alignment metrics to a JSON file.
    """
    if output_dir is None:
        output_dir = get_output_path("")
    
    output_path = Path(output_dir) / "alignment_metrics.json"
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved alignment metrics to {output_path}")
    return str(output_path)

def impute_descriptors_knn(df: pd.DataFrame, k: int = 5) -> Tuple[pd.DataFrame, List[int]]:
    """
    Impute missing descriptors using k-nearest-neighbors (k=5) based on structure-based similarity
    using Morgan fingerprints.
    
    Returns:
        Tuple of (imputed_df, excluded_indices)
    """
    # Identify descriptor columns (exclude composition, surface_facet, energy_change, etc.)
    # We assume numeric columns are descriptors
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric descriptor columns found for imputation.")
        return df, []
    
    # Generate fingerprints for all rows to calculate distance
    # We need a column of fingerprints or calculate on the fly
    # Assuming 'smiles' or similar is present to generate fingerprints
    if 'smiles' not in df.columns:
        # Try to infer from composition? No, we need smiles for fingerprints.
        # If not present, we cannot do structure-based similarity.
        # Fallback to standard KNN on numeric features if smiles missing?
        # The task says "based on structure-based similarity using Morgan fingerprints".
        # If smiles is missing, we cannot do this.
        raise ValueError("Column 'smiles' required for Morgan fingerprint KNN imputation.")
    
    fingerprints = np.array([generate_morgan_fingerprint(s) for s in df['smiles']])
    
    # We need to calculate distance in fingerprint space
    # KNNImputer from sklearn works on the feature matrix.
    # We will create a feature matrix that includes the fingerprints + existing numeric descriptors.
    # But the task says "based on structure-based similarity... Calculate Euclidean distance in fingerprint space".
    # This implies the distance metric should be based on fingerprints.
    #
    # Approach:
    # 1. Create a matrix of fingerprints (or a subset if too large)
    # 2. Use this matrix to find neighbors for rows with missing descriptors.
    # 3. Impute the missing descriptors using the values of the neighbors.
    
    # Since we need to impute 'numeric_cols', we can use KNNImputer on the full feature set
    # but we need to ensure the distance is calculated on fingerprints.
    # sklearn KNNImputer uses Euclidean distance by default.
    # We can pass the fingerprint matrix as the data to find neighbors, but we need to impute the numeric_cols.
    #
    # Alternative:
    # 1. Identify rows with missing values in numeric_cols.
    # 2. For each such row, find k nearest neighbors in the fingerprint space among rows that have NO missing values in numeric_cols.
    # 3. Impute using the mean of the neighbors' values for the missing columns.
    
    # Let's implement the explicit logic:
    mask_missing = df[numeric_cols].isna().any(axis=1)
    mask_complete = ~mask_missing
    
    if mask_missing.sum() == 0:
        logger.info("No missing values in descriptors to impute.")
        return df, []
    
    complete_indices = df.index[mask_complete].tolist()
    missing_indices = df.index[mask_missing].tolist()
    
    if len(complete_indices) < k:
        logger.warning(f"Only {len(complete_indices)} complete rows found, less than k={k}. Cannot impute.")
        # Exclude all missing rows
        return df, missing_indices
    
    # Extract fingerprints for complete and missing rows
    fp_complete = fingerprints[mask_complete]
    fp_missing = fingerprints[mask_missing]
    
    # Calculate distances
    # We need to map missing indices to their neighbors in complete indices
    excluded_indices = []
    
    # To optimize, we can use a simple loop or vectorized distance if feasible
    # Given the dataset size might be large, we do a simple loop for clarity
    # In production, use sklearn NearestNeighbors on the fingerprint matrix.
    from sklearn.neighbors import NearestNeighbors
    
    nbrs = NearestNeighbors(n_neighbors=k, algorithm='auto', metric='euclidean')
    nbrs.fit(fp_complete)
    
    distances, indices = nbrs.kneighbors(fp_missing)
    
    # Check if any row has no valid neighbors (distance is infinity or similar)
    # Neighbors should exist if we have enough complete rows
    
    imputed_data = df.copy()
    
    for i, idx in enumerate(missing_indices):
        neighbor_indices = indices[i]
        # Map back to original dataframe indices
        neighbor_orig_indices = [complete_indices[n] for n in neighbor_indices]
        
        # Get the values of the neighbors for the numeric columns
        neighbor_values = df.loc[neighbor_orig_indices, numeric_cols].values
        
        # Calculate mean of neighbors for each column
        mean_values = np.nanmean(neighbor_values, axis=0)
        
        # Check if any neighbor was also missing (should not happen if mask_complete is correct)
        # But if k neighbors were found, we assume they are complete.
        
        # Assign the mean values
        imputed_data.loc[idx, numeric_cols] = mean_values
    
    # If any row could not be imputed (e.g. all neighbors were missing, though we filtered),
    # we would add to excluded_indices. Here we assume success if k neighbors found.
    # However, the task says: "If <5 neighbors exist, flag and exclude from training set."
    # We handled this by checking len(complete_indices) < k at the start.
    # If a specific row has NaN in the neighbor calculation (e.g. all neighbors missing that specific col),
    # we might still have NaN.
    
    final_missing = imputed_data[numeric_cols].isna().any(axis=1)
    if final_missing.sum() > 0:
        logger.warning(f"Still have {final_missing.sum()} rows with missing values after imputation.")
        excluded_indices.extend(imputed_data.index[final_missing].tolist())
        imputed_data = imputed_data[~final_missing]
    
    return imputed_data, excluded_indices

def scale_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scale all numeric features to zero mean and unit variance.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return df
    
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df

def main():
    """
    Main entry point for the preprocessing pipeline.
    """
    logger.info("Starting preprocessing pipeline (T014).")
    
    try:
        # 1. Load data
        df = load_raw_oc20_data()
        
        # 2. Align entries and apply FR-002 exclusion
        aligned_df, exclusion_log = align_entries(df)
        
        # 3. Save exclusion log (CRITICAL for T014)
        save_exclusion_log(exclusion_log)
        
        # 4. Compute and save metrics (even if 0 aligned)
        total = len(df)
        aligned_count = len(aligned_df)
        success_rate = compute_alignment_success_rate(total, aligned_count)
        save_alignment_metrics({
            "total_entries": total,
            "aligned_entries": aligned_count,
            "excluded_by_fr002": len(exclusion_log),
            "success_rate": success_rate
        })
        
        if aligned_count == 0:
            logger.warning("No entries remain after FR-002 exclusion. Pipeline may stop here.")
            # We still return the empty dataframe to allow downstream steps to handle it or fail gracefully
            return aligned_df
        
        # 5. Retrieve target
        aligned_df = retrieve_target_variable(aligned_df)
        
        # 6. Impute descriptors
        aligned_df, excluded_impute = impute_descriptors_knn(aligned_df)
        if excluded_impute:
            logger.warning(f"Excluded {len(excluded_impute)} rows due to insufficient neighbors for imputation.")
        
        # 7. Scale features
        aligned_df = scale_features(aligned_df)
        
        logger.info("Preprocessing pipeline completed successfully.")
        return aligned_df
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
