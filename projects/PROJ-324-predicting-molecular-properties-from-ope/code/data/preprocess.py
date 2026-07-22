"""
Preprocessing module for molecular data.
Implements filtering for high-confidence measurements and detection of missing physical covariates.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONFIDENCE_THRESHOLD = 0.8
PHYSICAL_COVARIATES = ['pH', 'temperature', 'pressure']

def ensure_dirs():
    """Ensure output directories exist."""
    data_derived = Path('data/derived')
    data_derived.mkdir(parents=True, exist_ok=True)

def load_preprocessed_data(input_path: str) -> pd.DataFrame:
    """
    Load preprocessed data from a CSV file.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        DataFrame with preprocessed molecular data.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records")
    return df

def filter_high_confidence(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter entries based on confidence score.
    
    Args:
        df: Input DataFrame with 'confidence_score' column (if available).
        
    Returns:
        Tuple of (filtered_df, excluded_df)
    """
    if 'confidence_score' in df.columns:
        # Filter for high confidence entries
        high_conf_mask = df['confidence_score'] >= CONFIDENCE_THRESHOLD
        filtered_df = df[high_conf_mask].copy()
        excluded_df = df[~high_conf_mask].copy()
        logger.info(f"Filtered by confidence: {len(filtered_df)} kept, {len(excluded_df)} excluded")
    else:
        # No confidence score column, keep all but log
        filtered_df = df.copy()
        excluded_df = pd.DataFrame(columns=df.columns)
        logger.warning("No 'confidence_score' column found. Keeping all entries.")
    
    return filtered_df, excluded_df

def handle_missing_values(df: pd.DataFrame, target_properties: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Handle entries with missing target property values.
    
    Args:
        df: Input DataFrame.
        target_properties: List of target property column names.
        
    Returns:
        Tuple of (cleaned_df, excluded_df)
    """
    # Check for missing target properties
    mask_missing = pd.DataFrame(False, index=df.index, columns=target_properties)
    for prop in target_properties:
        if prop in df.columns:
            mask_missing[prop] = df[prop].isna()
        else:
            # Column doesn't exist, treat all as missing
            mask_missing[prop] = True
    
    # Any row with missing target property
    any_missing = mask_missing.any(axis=1)
    cleaned_df = df[~any_missing].copy()
    excluded_df = df[any_missing].copy()
    
    logger.info(f"Filtered missing values: {len(cleaned_df)} kept, {len(excluded_df)} excluded")
    return cleaned_df, excluded_df

def detect_missing_covariates(df: pd.DataFrame) -> pd.Series:
    """
    Detect missing physical covariates (pH, temperature, pressure) in the source data.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Series of lists containing names of missing covariates for each row.
    """
    missing_lists = []
    for idx, row in df.iterrows():
        missing = []
        for covariate in PHYSICAL_COVARIATES:
            if covariate not in df.columns:
                missing.append(covariate)
            elif pd.isna(row.get(covariate)):
                missing.append(covariate)
        missing_lists.append(missing)
    
    return pd.Series(missing_lists, index=df.index)

def generate_quality_report(
    df: pd.DataFrame,
    excluded_entries: List[Dict[str, Any]],
    missing_covariates_map: pd.Series
) -> pd.DataFrame:
    """
    Generate the data quality report CSV.
    
    Args:
        df: The kept DataFrame (for reference).
        excluded_entries: List of dictionaries representing excluded rows with reasons.
        missing_covariates_map: Series mapping index to list of missing covariates.
        
    Returns:
        DataFrame for the quality report.
    """
    report_data = []
    
    # Process excluded entries
    for entry in excluded_entries:
        smiles = entry.get('smiles', 'N/A')
        exclusion_reason = entry.get('exclusion_reason', 'Unknown')
        
        # Get missing covariates for this entry if index is available
        missing_covs = []
        if 'index' in entry:
            idx = entry['index']
            if idx in missing_covariates_map.index:
                missing_covs = missing_covariates_map.loc[idx]
        
        report_data.append({
            'smiles': smiles,
            'exclusion_reason': exclusion_reason,
            'missing_covariate_list': str(missing_covs),
            'experimental_flag': True  # Marked as experimental source check
        })
    
    report_df = pd.DataFrame(report_data)
    return report_df

def save_quality_report(report_df: pd.DataFrame, output_path: str):
    """
    Save the data quality report to CSV.
    
    Args:
        report_df: The report DataFrame.
        output_path: Path to save the CSV file.
    """
    report_df.to_csv(output_path, index=False)
    logger.info(f"Quality report saved to {output_path}")

def tanimoto_similarity(fp1: List[int], fp2: List[int]) -> float:
    """
    Calculate Tanimoto similarity between two binary fingerprints.
    
    Args:
        fp1: First fingerprint (list of 0/1).
        fp2: Second fingerprint (list of 0/1).
        
    Returns:
        Tanimoto similarity score.
    """
    if len(fp1) != len(fp2):
        raise ValueError("Fingerprints must be of the same length")
    
    intersection = sum(a & b for a, b in zip(fp1, fp2))
    union = sum(a | b for a, b in zip(fp1, fp2))
    
    if union == 0:
        return 0.0
    return intersection / union

def maxmin_sampling(
    df: pd.DataFrame, 
    target_size: int, 
    similarity_threshold: float = 0.7
) -> pd.DataFrame:
    """
    Perform MaxMin sampling to select a diverse subset of molecules.
    
    Args:
        df: DataFrame with 'smiles' column.
        target_size: Desired number of molecules in the diverse set.
        similarity_threshold: Maximum allowed Tanimoto similarity.
        
    Returns:
        DataFrame with the diverse subset.
    """
    logger.info(f"Starting MaxMin sampling for {target_size} molecules...")
    
    if len(df) <= target_size:
        logger.info("Dataset size is smaller than target, returning full set.")
        return df
    
    # Simple heuristic: shuffle and filter iteratively
    # Note: A full MaxMin implementation requires pairwise distances which is O(N^2)
    # For large N, we use a greedy approximation
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    selected = [df_shuffled.iloc[0]]
    candidates = df_shuffled.iloc[1:].copy()
    
    # Convert SMILES to RDKit molecules
    mols = [Chem.MolFromSmiles(smiles) for smiles in df_shuffled['smiles']]
    if any(m is None for m in mols):
        logger.warning("Some SMILES could not be parsed. Filtering invalid molecules.")
        valid_indices = [i for i, m in enumerate(mols) if m is not None]
        df_shuffled = df_shuffled.iloc[valid_indices].reset_index(drop=True)
        mols = [m for m in mols if m is not None]
        candidates = df_shuffled.iloc[1:].copy()
        selected = [df_shuffled.iloc[0]]
    
    # Compute Morgan fingerprints for efficiency
    fps = [rdMolDescriptors.GetMorganFingerprintAsBitVect(m, 2, nBits=2048) for m in mols]
    
    selected_fps = [fps[0]]
    selected_indices = [0]
    
    while len(selected) < target_size and len(candidates) > 0:
        # Calculate minimum distance from each candidate to the selected set
        min_dists = []
        for i, cand_fp in enumerate(fps[len(selected):]):
            max_sim = 0.0
            for sel_fp in selected_fps:
                sim = tanimoto_similarity(list(sel_fp), list(cand_fp))
                if sim > max_sim:
                    max_sim = sim
            min_dists.append(max_sim)
        
        # Select the candidate with the maximum minimum distance
        best_idx = np.argmax(min_dists)
        if min_dists[best_idx] > similarity_threshold:
            # Stop if all remaining candidates are too similar
            break
        
        selected.append(candidates.iloc[best_idx])
        selected_fps.append(fps[len(selected)])
        selected_indices.append(len(selected) - 1 + len(candidates) - len(min_dists)) # Simplified logic
        candidates = candidates.drop(candidates.index[best_idx]).reset_index(drop=True)
        # Adjust fps list to remove used candidate (inefficient but simple)
        fps.pop(len(selected) - 1) 
    
    logger.info(f"MaxMin sampling complete: {len(selected)} molecules selected.")
    return pd.DataFrame(selected)

def save_processed_data(df: pd.DataFrame, output_path: str):
    """
    Save the processed DataFrame to CSV.
    
    Args:
        df: Processed DataFrame.
        output_path: Path to save the CSV file.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

def main():
    """
    Main entry point for the preprocessing pipeline.
    """
    ensure_dirs()
    
    # Configuration
    input_file = "data/raw/chembl_dataset.csv" # Example path, adjust based on T008 output
    output_file = "data/derived/preprocessed_data.csv"
    report_file = "data/derived/data_quality_report.csv"
    
    # Check if input exists (for demonstration, we assume T008 created it)
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found. Please run T008 first.")
        # In a real run, this would fail loudly. 
        # For this task implementation, we proceed with logic assuming file exists.
        # If the runner executes this and the file is missing, it will crash as intended.
        raise FileNotFoundError(f"Input file {input_file} not found.")

    # Load data
    df = load_preprocessed_data(input_file)
    
    target_properties = ['logP', 'solubility', 'boiling_point']
    
    # Step 1: Filter high confidence
    df_conf, excluded_conf = filter_high_confidence(df)
    
    # Step 2: Handle missing values
    df_clean, excluded_missing = handle_missing_values(df_conf, target_properties)
    
    # Combine excluded entries
    excluded_entries = []
    for _, row in excluded_conf.iterrows():
        excluded_entries.append({
            'smiles': row.get('smiles', ''),
            'exclusion_reason': 'Low confidence',
            'index': row.name
        })
    for _, row in excluded_missing.iterrows():
        excluded_entries.append({
            'smiles': row.get('smiles', ''),
            'exclusion_reason': 'Missing target property',
            'index': row.name
        })
    
    # Step 3: Detect missing covariates
    missing_covs_map = detect_missing_covariates(df_clean)
    
    # Log missing covariates
    missing_counts = {cov: 0 for cov in PHYSICAL_COVARIATES}
    for cov in PHYSICAL_COVARIATES:
        if cov not in df_clean.columns:
            missing_counts[cov] = len(df_clean)
            logger.warning(f"Field '{cov}' is completely missing from the dataset.")
        else:
            missing_counts[cov] = df_clean[cov].isna().sum()
            if missing_counts[cov] > 0:
                logger.warning(f"Field '{cov}' has {missing_counts[cov]} missing values.")
    
    # Generate and save quality report
    report_df = generate_quality_report(df_clean, excluded_entries, missing_covs_map)
    save_quality_report(report_df, report_file)
    
    # Save processed data
    save_processed_data(df_clean, output_file)
    
    logger.info("Preprocessing complete.")
    return df_clean, report_df

if __name__ == "__main__":
    main()