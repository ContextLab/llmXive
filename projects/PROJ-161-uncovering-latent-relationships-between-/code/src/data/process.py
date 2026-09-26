"""
Data processing module for molecular descriptor computation and SMILES canonicalization.

This module handles:
- SMILES canonicalization using RDKit
- Calculation of standardized RDKit descriptors
- Filtering of invalid compounds
- Merging structure and resistance data on InChIKey
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger

from src.config import get_project_root, get_data_processed_path
from src.data.schema import load_data_version_from_file, save_data_version_to_file

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)

# Standardized set of RDKit descriptors from descList
# These are the standard descriptors available in rdkit.Chem.Descriptors.descList
DESCRIPTOR_NAMES = [name for name, _ in Descriptors.descList]


def canonicalize_smiles(smiles_list: List[str]) -> Tuple[List[Optional[str]], List[int]]:
    """
    Canonicalize a list of SMILES strings.

    Args:
        smiles_list: List of SMILES strings to canonicalize

    Returns:
        Tuple of (canonicalized_list, invalid_indices)
        - canonicalized_list: List where valid SMILES are canonicalized, invalid are None
        - invalid_indices: List of indices where SMILES were invalid
    """
    canonicalized = []
    invalid_indices = []

    for i, smiles in enumerate(smiles_list):
        if pd.isna(smiles) or not isinstance(smiles, str) or not smiles.strip():
            canonicalized.append(None)
            invalid_indices.append(i)
            continue

        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                canonicalized.append(None)
                invalid_indices.append(i)
            else:
                canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
                canonicalized.append(canonical_smiles)
        except Exception as e:
            logger.warning(f"Failed to canonicalize SMILES at index {i}: {e}")
            canonicalized.append(None)
            invalid_indices.append(i)

    return canonicalized, invalid_indices


def calculate_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """
    Calculate all standard RDKit descriptors for a molecule.

    Args:
        mol: RDKit Mol object

    Returns:
        Dictionary mapping descriptor names to values
    """
    descriptors = {}
    for name, func in Descriptors.descList:
        try:
            descriptors[name] = func(mol)
        except Exception as e:
            # If a descriptor fails, set to NaN and log
            descriptors[name] = np.nan
            logger.debug(f"Descriptor {name} failed: {e}")

    return descriptors


def process_compounds(smiles_list: List[str]) -> pd.DataFrame:
    """
    Process a list of SMILES: canonicalize and calculate descriptors.

    Args:
        smiles_list: List of SMILES strings

    Returns:
        DataFrame with columns: 'InChIKey', canonicalized SMILES, and all descriptors
    """
    logger.info(f"Processing {len(smiles_list)} compounds...")

    # Canonicalize SMILES
    canonicalized, invalid_indices = canonicalize_smiles(smiles_list)
    logger.info(f"Canonicalized {len(canonicalized) - len(invalid_indices)} compounds, "
                f"excluded {len(invalid_indices)} invalid")

    # Filter out invalid compounds
    valid_indices = [i for i in range(len(canonicalized)) if canonicalized[i] is not None]
    valid_smiles = [canonicalized[i] for i in valid_indices]

    if not valid_smiles:
        logger.warning("No valid compounds found!")
        return pd.DataFrame()

    # Calculate descriptors for valid compounds
    logger.info("Calculating RDKit descriptors...")
    data_rows = []
    for i, smiles in enumerate(valid_smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        # Generate InChIKey for merging
        try:
            inchi = Chem.MolToInchi(mol)
            inchikey = Chem.InchiToInchiKey(inchi)
        except Exception as e:
            logger.warning(f"Failed to generate InChIKey for {smiles}: {e}")
            continue

        # Calculate descriptors
        desc_dict = calculate_descriptors(mol)
        desc_dict['InChIKey'] = inchikey
        desc_dict['SMILES'] = smiles
        data_rows.append(desc_dict)

    if not data_rows:
        logger.warning("No compounds could be processed after descriptor calculation!")
        return pd.DataFrame()

    # Create DataFrame
    df = pd.DataFrame(data_rows)

    # Ensure InChIKey is first column
    cols = ['InChIKey', 'SMILES'] + [c for c in df.columns if c not in ['InChIKey', 'SMILES']]
    df = df[cols]

    logger.info(f"Processed {len(df)} compounds with {len(DESCRIPTOR_NAMES)} descriptors")
    return df


def merge_structure_and_resistance(structure_df: pd.DataFrame,
                                   resistance_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Merge structure data with resistance data on InChIKey.

    Args:
        structure_df: DataFrame with molecular descriptors and InChIKey
        resistance_df: DataFrame with resistance frequencies and InChIKey

    Returns:
        Tuple of (merged_df, metrics_dict)
        - merged_df: Merged DataFrame with NaN for missing resistance data
        - metrics_dict: Dictionary with merge statistics
    """
    logger.info(f"Merging structure data ({len(structure_df)} rows) with "
                f"resistance data ({len(resistance_df)} rows)")

    # Ensure InChIKey is string for merging
    structure_df = structure_df.copy()
    resistance_df = resistance_df.copy()
    structure_df['InChIKey'] = structure_df['InChIKey'].astype(str)
    resistance_df['InChIKey'] = resistance_df['InChIKey'].astype(str)

    # Perform left join to keep all structures
    merged_df = pd.merge(
        structure_df,
        resistance_df,
        on='InChIKey',
        how='left'
    )

    # Calculate metrics
    total_requested = len(structure_df)
    matches = merged_df['InChIKey'].notna().sum()  # All should have InChIKey
    matched_resistance = merged_df[merged_df.columns[~merged_df.columns.isin(['InChIKey', 'SMILES'] + DESCRIPTOR_NAMES)]]
    resistance_non_null = merged_df[~merged_df[merged_df.columns[~merged_df.columns.isin(['InChIKey', 'SMILES'] + DESCRIPTOR_NAMES)]].isna().all(axis=1)]

    metrics = {
        'total_requested': total_requested,
        'matches': len(merged_df),
        'with_resistance_data': len(resistance_non_null),
        'fraction_with_resistance': len(resistance_non_null) / total_requested if total_requested > 0 else 0.0
    }

    logger.info(f"Merge complete: {metrics['with_resistance_data']} of {total_requested} "
                f"compounds have resistance data ({metrics['fraction_with_resistance']:.2%})")

    return merged_df, metrics


def run_process_pipeline(chembl_path: Optional[str] = None,
                         zinc_path: Optional[str] = None,
                         ncbi_path: Optional[str] = None,
                         output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run the full processing pipeline: load, canonicalize, calculate descriptors, merge.

    Args:
        chembl_path: Path to ChEMBL SMILES file (optional)
        zinc_path: Path to ZINC15 SMILES file (optional)
        ncbi_path: Path to NCBI resistance data file (optional)
        output_path: Path to save processed data (optional, defaults to config)

    Returns:
        Processed DataFrame
    """
    project_root = get_project_root()
    processed_dir = get_data_processed_path()

    # Load structure data (ChEMBL and/or ZINC15)
    all_structures = []

    if chembl_path:
        chembl_path = Path(chembl_path)
        if chembl_path.exists():
            logger.info(f"Loading ChEMBL data from {chembl_path}")
            df_chembl = pd.read_csv(chembl_path)
            if 'SMILES' in df_chembl.columns:
                all_structures.append(df_chembl['SMILES'].tolist())
            else:
                logger.warning(f"ChEMBL file {chembl_path} has no SMILES column")

    if zinc_path:
        zinc_path = Path(zinc_path)
        if zinc_path.exists():
            logger.info(f"Loading ZINC15 data from {zinc_path}")
            df_zinc = pd.read_csv(zinc_path)
            if 'SMILES' in df_zinc.columns:
                all_structures.append(df_zinc['SMILES'].tolist())
            else:
                logger.warning(f"ZINC15 file {zinc_path} has no SMILES column")

    if not all_structures:
        raise ValueError("No structure data files provided or found")

    # Combine all SMILES
    all_smiles = []
    for structure_list in all_structures:
        all_smiles.extend(structure_list)

    logger.info(f"Total SMILES to process: {len(all_smiles)}")

    # Process compounds
    structure_df = process_compounds(all_smiles)

    if structure_df.empty:
        raise ValueError("No valid compounds could be processed")

    # Merge with resistance data if provided
    if ncbi_path:
        ncbi_path = Path(ncbi_path)
        if ncbi_path.exists():
            logger.info(f"Loading NCBI resistance data from {ncbi_path}")
            resistance_df = pd.read_csv(ncbi_path)

            # Standardize column names if needed
            if 'InChIKey' not in resistance_df.columns:
                # Try to find a similar column
                for col in resistance_df.columns:
                    if 'inchi' in col.lower() or 'key' in col.lower():
                        resistance_df = resistance_df.rename(columns={col: 'InChIKey'})
                        break

            if 'InChIKey' in resistance_df.columns:
                structure_df, metrics = merge_structure_and_resistance(structure_df, resistance_df)

                # Save merge metrics
                metrics_path = processed_dir / 'merge_metrics.json'
                import json
                with open(metrics_path, 'w') as f:
                    json.dump(metrics, f, indent=2)
                logger.info(f"Saved merge metrics to {metrics_path}")
            else:
                logger.warning("NCBI file has no InChIKey column, skipping merge")
    else:
        logger.info("No NCBI path provided, skipping resistance merge")

    # Save processed data
    if output_path is None:
        output_path = processed_dir / 'descriptors.csv'
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    structure_df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

    return structure_df


def main():
    """Main entry point for the processing pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = get_project_root()
    processed_dir = get_data_processed_path()

    # Default paths based on download.py outputs
    chembl_path = project_root / 'data' / 'raw' / 'chembl_smiles.csv'
    zinc_path = project_root / 'data' / 'raw' / 'zinc15_smiles.csv'
    ncbi_path = project_root / 'data' / 'raw' / 'ncbi_resistance.csv'
    output_path = processed_dir / 'descriptors.csv'

    # Check if any structure data exists
    if not chembl_path.exists() and not zinc_path.exists():
        logger.error("No structure data found. Please run download.py first.")
        return

    try:
        df = run_process_pipeline(
            chembl_path=str(chembl_path) if chembl_path.exists() else None,
            zinc_path=str(zinc_path) if zinc_path.exists() else None,
            ncbi_path=str(ncbi_path) if ncbi_path.exists() else None,
            output_path=str(output_path)
        )
        logger.info(f"Pipeline completed successfully. Processed {len(df)} compounds.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
