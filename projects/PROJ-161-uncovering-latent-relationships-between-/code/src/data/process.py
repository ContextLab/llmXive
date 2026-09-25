import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import RDLogger

from src.config import get_project_root, get_data_raw_path, get_data_processed_path
from src.data.schema import load_data_version_from_file

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)


def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    Canonicalize a SMILES string.
    Returns None if the SMILES is invalid.
    """
    if not isinstance(smiles, str) or pd.isna(smiles):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, isomericSmiles=True)
    except Exception:
        return None


def calculate_descriptors(smiles: str) -> Dict[str, float]:
    """
    Calculate a standard set of RDKit descriptors for a valid SMILES.
    Returns a dictionary of descriptor_name: value.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}
    
    descriptors = {}
    for name, func in Descriptors.descList:
        try:
            val = func(mol)
            # Ensure numeric, handle potential NaNs from RDKit
            if isinstance(val, (int, float)) and not np.isnan(val):
                descriptors[name] = float(val)
            else:
                descriptors[name] = 0.0
        except Exception:
            # If a descriptor calculation fails, skip it or set to 0
            descriptors[name] = 0.0
    return descriptors


def process_compounds(smiles_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame of SMILES: canonicalize, calculate descriptors, and add InChIKey.
    Excludes invalid compounds.
    """
    logger.info(f"Processing {len(smiles_df)} compounds...")
    
    # Apply canonicalization
    smiles_df = smiles_df.copy()
    smiles_df['canonical_smiles'] = smiles_df['smiles'].apply(canonicalize_smiles)
    
    # Filter out invalid SMILES
    valid_mask = smiles_df['canonical_smiles'].notna()
    valid_df = smiles_df[valid_mask].reset_index(drop=True)
    logger.info(f"Valid compounds: {len(valid_df)} (excluded {len(smiles_df) - len(valid_df)})")
    
    if valid_df.empty:
        return pd.DataFrame()
    
    # Calculate InChIKey for merging
    def get_inchi_key(smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return Chem.MolToInchiKey(mol)
        return None
    
    valid_df['inchi_key'] = valid_df['canonical_smiles'].apply(get_inchi_key)
    valid_df = valid_df[valid_df['inchi_key'].notna()].reset_index(drop=True)
    logger.info(f"Compounds with valid InChIKey: {len(valid_df)}")
    
    # Calculate descriptors
    logger.info("Calculating descriptors...")
    descriptor_records = []
    for idx, row in valid_df.iterrows():
        if idx % 1000 == 0:
            logger.info(f"Processed {idx}/{len(valid_df)} compounds for descriptors")
        descs = calculate_descriptors(row['canonical_smiles'])
        if descs:
            record = {
                'inchi_key': row['inchi_key'],
                'canonical_smiles': row['canonical_smiles']
            }
            record.update(descs)
            descriptor_records.append(record)
    
    if not descriptor_records:
        logger.warning("No descriptors calculated.")
        return pd.DataFrame()
    
    descriptors_df = pd.DataFrame(descriptor_records)
    logger.info(f"Descriptor matrix shape: {descriptors_df.shape}")
    return descriptors_df


def merge_structure_and_resistance(structure_df: pd.DataFrame, 
                                   resistance_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Join structure data (descriptors) and resistance data on InChIKey.
    Flags missing resistance as NaN.
    
    Args:
        structure_df: DataFrame with 'inchi_key' and descriptor columns.
        resistance_df: DataFrame with 'inchi_key' and resistance metrics.
        
    Returns:
        merged_df: The merged DataFrame.
        metrics: Dictionary with merge statistics.
    """
    if structure_df.empty:
        logger.warning("Structure DataFrame is empty. Returning empty result.")
        return pd.DataFrame(), {'total_requested': 0, 'matches': 0, 'fraction': 0.0}
    
    if resistance_df.empty:
        logger.warning("Resistance DataFrame is empty. Returning empty result.")
        return pd.DataFrame(), {'total_requested': len(structure_df), 'matches': 0, 'fraction': 0.0}

    # Ensure InChIKey is string for consistent merging
    structure_df = structure_df.copy()
    resistance_df = resistance_df.copy()
    structure_df['inchi_key'] = structure_df['inchi_key'].astype(str)
    resistance_df['inchi_key'] = resistance_df['inchi_key'].astype(str)

    total_requested = len(structure_df)
    
    # Perform left join to keep all structures, flagging missing resistance
    merged_df = pd.merge(
        structure_df,
        resistance_df,
        on='inchi_key',
        how='left'
    )
    
    matches = merged_df['inchi_key'].nunique()
    # Since it's a left join, matches in the context of "having resistance" 
    # is the count of non-NaN resistance entries. 
    # However, the task says "flagging missing resistance as NaN", implying
    # we keep the structure even if resistance is missing.
    # Let's count how many rows have valid resistance data.
    # Assuming resistance data columns are not 'inchi_key' and 'canonical_smiles'
    resistance_cols = [c for c in merged_df.columns if c not in structure_df.columns and c != 'inchi_key']
    
    if resistance_cols:
        has_resistance = merged_df[resistance_cols[0]].notna().sum()
    else:
        has_resistance = 0

    fraction = has_resistance / total_requested if total_requested > 0 else 0.0
    
    metrics = {
        'total_requested': total_requested,
        'matches': has_resistance,
        'fraction': fraction,
        'total_merged_rows': len(merged_df)
    }
    
    logger.info(f"Merge complete: {has_resistance}/{total_requested} matches ({fraction:.2%})")
    return merged_df, metrics


def run_process_pipeline() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main pipeline function:
    1. Load downloaded raw data (SMILES and Resistance).
    2. Process compounds (canonicalize, descriptors, InChIKey).
    3. Merge on InChIKey.
    4. Save intermediate and final outputs.
    
    Returns:
        merged_df: The final merged DataFrame.
        metrics: Merge metrics.
    """
    root = get_project_root()
    raw_path = get_data_raw_path()
    processed_path = get_data_processed_path()
    
    # Ensure directories exist
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Load raw SMILES data (assumed to be downloaded by T013)
    # Expected file: data/raw/chembl_smiles.csv or similar
    # We need to identify the specific file name from the download step.
    # Assuming standard naming based on T013:
    chembl_file = raw_path / "chembl_smiles.csv"
    zinc_file = raw_path / "zinc15_smiles.csv"
    ncbi_file = raw_path / "ncbi_resistance_frequencies.csv"
    
    if not chembl_file.exists() and not zinc_file.exists():
        raise FileNotFoundError(f"Raw SMILES files not found in {raw_path}. "
                                f"Run download pipeline first.")
    
    # Load and combine SMILES sources
    smiles_dfs = []
    if chembl_file.exists():
        df = pd.read_csv(chembl_file)
        if 'smiles' in df.columns:
            smiles_dfs.append(df)
        else:
            logger.warning(f"{chembl_file} does not contain 'smiles' column.")
    
    if zinc_file.exists():
        df = pd.read_csv(zinc_file)
        if 'smiles' in df.columns:
            smiles_dfs.append(df)
        else:
            logger.warning(f"{zinc_file} does not contain 'smiles' column.")
    
    if not smiles_dfs:
        raise ValueError("No valid SMILES data found.")
    
    all_smiles_df = pd.concat(smiles_dfs, ignore_index=True)
    logger.info(f"Loaded {len(all_smiles_df)} total SMILES entries.")
    
    # Process compounds (T014 logic)
    processed_df = process_compounds(all_smiles_df)
    
    if processed_df.empty:
        logger.error("No valid compounds processed. Stopping.")
        return pd.DataFrame(), {}
    
    # Save processed descriptors (intermediate)
    descriptors_path = processed_path / "descriptors.csv"
    processed_df.to_csv(descriptors_path, index=False)
    logger.info(f"Saved descriptors to {descriptors_path}")
    
    # Load resistance data
    if not ncbi_file.exists():
        raise FileNotFoundError(f"Resistance data file not found: {ncbi_file}. "
                                f"Run download pipeline first.")
    
    resistance_df = pd.read_csv(ncbi_file)
    logger.info(f"Loaded {len(resistance_df)} resistance entries.")
    
    # Merge (T015 logic)
    merged_df, metrics = merge_structure_and_resistance(processed_df, resistance_df)
    
    if merged_df.empty:
        logger.warning("Merge resulted in empty DataFrame.")
        return pd.DataFrame(), metrics
    
    # Save merged data
    merged_path = processed_path / "merged_data.csv"
    merged_df.to_csv(merged_path, index=False)
    logger.info(f"Saved merged data to {merged_path}")
    
    # Save metrics (T016 logic - generating the metrics file)
    metrics_path = processed_path / "merge_metrics.json"
    import json
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved merge metrics to {metrics_path}")
    
    return merged_df, metrics


def main():
    """Entry point for running the process pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        merged_df, metrics = run_process_pipeline()
        if not merged_df.empty:
            logger.info("Pipeline completed successfully.")
            logger.info(f"Final dataset shape: {merged_df.shape}")
            logger.info(f"Merge fraction: {metrics.get('fraction', 0):.2%}")
        else:
            logger.error("Pipeline finished but no data was merged.")
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
