"""
Feature Engineering Module for Molecular Halide Binding Affinity Prediction.

This module generates molecular descriptors and fingerprints for host molecules
using RDKit. It computes ECFP fingerprints and specific physicochemical descriptors
including charge_density and cavity_volume.

Dependencies:
    - rdkit
    - pandas
    - numpy
    - scikit-learn

Output:
    - data/processed/halide_binding_features.csv: DataFrame with SMILES, descriptors, and fingerprints.
"""

import os
import logging
import pickle
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit import DataStructs

# Import project utilities
from code.utils.logger import get_logger
from code.utils.config import get_data_path, get_code_path

# Initialize logger
logger = get_logger(__name__)


def parse_smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit Mol object.

    Args:
        smiles: SMILES string representation of the molecule.

    Returns:
        RDKit Mol object or None if parsing fails.
    """
    if not isinstance(smiles, str) or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None
        # Add hydrogens for better descriptor calculation
        mol = Chem.AddHs(mol)
        return mol
    except Exception as e:
        logger.error(f"Error parsing SMILES '{smiles}': {e}")
        return None


def calculate_charge_density(mol: Chem.Mol) -> float:
    """
    Calculate a proxy for charge density based on molecular properties.
    Uses the ratio of partial charge magnitude (approximated by heteroatom count)
    to molecular volume (approximated by MolWt).

    Note: RDKit does not have a direct 'charge_density' descriptor.
    We approximate it as (Number of Heteroatoms) / (Molecular Weight).
    This captures the concept of charge concentration relative to size.

    Args:
        mol: RDKit Mol object.

    Returns:
        Float representing the charge density proxy.
    """
    if mol is None:
        return 0.0

    try:
        # Count heteroatoms (non-C, non-H) as a proxy for charge centers
        # Heteroatoms are typically where partial charges reside
        heteroatom_count = sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() not in (1, 6))

        # Get molecular weight as a proxy for volume/size
        mol_weight = Descriptors.MolWt(mol)

        if mol_weight <= 0:
            return 0.0

        # Charge density proxy: heteroatoms per unit mass
        charge_density = heteroatom_count / mol_weight
        return float(charge_density)
    except Exception as e:
        logger.warning(f"Could not calculate charge density for molecule: {e}")
        return 0.0


def calculate_cavity_volume(mol: Chem.Mol) -> float:
    """
    Calculate a proxy for cavity volume using the Molecular Surface Area (SASA).
    RDKit's SASA is a standard measure of the accessible surface area, which
    correlates with the volume available for binding interactions.

    Alternatively, we can use the Van der Waals volume if available, but SASA
    is more robust for diverse organic molecules.

    Args:
        mol: RDKit Mol object.

    Returns:
        Float representing the cavity volume proxy (SASA).
    """
    if mol is None:
        return 0.0

    try:
        # Calculate SASA (Solvent Accessible Surface Area)
        # This serves as a proxy for the cavity/surface available for interaction
        sasa = rdMolDescriptors.CalcSASA(mol)
        return float(sasa)
    except Exception as e:
        logger.warning(f"Could not calculate cavity volume (SASA) for molecule: {e}")
        # Fallback to a simple volume approximation if SASA fails
        try:
            # Approximate volume using MolVolume if available, else 0
            # rdMolDescriptors does not have a direct volume calc in all versions,
            # so we rely on SASA. If that fails, return 0.
            return 0.0
        except Exception:
            return 0.0


def generate_ecfp_fingerprint(mol: Chem.Mol, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate an ECFP (Extended Connectivity Fingerprint) for a molecule.

    Args:
        mol: RDKit Mol object.
        radius: Radius of the fingerprint (ECFP4 = radius 2).
        n_bits: Length of the fingerprint vector.

    Returns:
        Numpy array (n_bits,) of 0s and 1s representing the fingerprint.
    """
    if mol is None:
        return np.zeros(n_bits, dtype=np.uint8)

    try:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        # Convert to numpy array
        arr = np.zeros((n_bits,), dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.error(f"Error generating ECFP fingerprint: {e}")
        return np.zeros(n_bits, dtype=np.uint8)


def calculate_rdkit_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """
    Calculate a standard set of RDKit descriptors.

    Args:
        mol: RDKit Mol object.

    Returns:
        Dictionary of descriptor names and values.
    """
    if mol is None:
        return {}

    descriptors = {}
    try:
        # Basic descriptors
        descriptors['MolWt'] = Descriptors.MolWt(mol)
        descriptors['LogP'] = Descriptors.MolLogP(mol)
        descriptors['NumHDonors'] = Descriptors.NumHDonors(mol)
        descriptors['NumHAcceptors'] = Descriptors.NumHAcceptors(mol)
        descriptors['TPSA'] = Descriptors.TPSA(mol)
        descriptors['NumRotatableBonds'] = Descriptors.NumRotatableBonds(mol)
        descriptors['NumAromaticRings'] = Descriptors.NumAromaticRings(mol)
        descriptors['NumAliphaticRings'] = Descriptors.NumAliphaticRings(mol)

        # Custom proxies
        descriptors['charge_density'] = calculate_charge_density(mol)
        descriptors['cavity_volume'] = calculate_cavity_volume(mol)

    except Exception as e:
        logger.error(f"Error calculating descriptors: {e}")

    return descriptors


def process_host_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the input DataFrame to generate molecular descriptors and fingerprints.

    Args:
        df: DataFrame containing 'host_smiles' column (and potentially others).

    Returns:
        DataFrame with added descriptor columns and fingerprint column.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    logger.info(f"Processing {len(df)} host molecules for feature engineering...")

    # Initialize lists to store results
    descriptors_list = []
    fingerprints_list = []
    valid_indices = []

    for idx, row in df.iterrows():
        smiles = row.get('host_smiles')
        if pd.isna(smiles):
            logger.warning(f"Row {idx} has missing SMILES, skipping.")
            continue

        mol = parse_smiles_to_mol(smiles)
        if mol is None:
            logger.warning(f"Row {idx} has invalid SMILES, skipping.")
            continue

        # Calculate descriptors
        desc = calculate_rdkit_descriptors(mol)
        descriptors_list.append(desc)

        # Generate fingerprint
        fp = generate_ecfp_fingerprint(mol)
        fingerprints_list.append(fp)
        valid_indices.append(idx)

    if not descriptors_list:
        logger.error("No valid molecules found to process.")
        # Return original df with nulls if possible, or empty
        return pd.DataFrame()

    # Create a DataFrame from descriptors
    desc_df = pd.DataFrame(descriptors_list, index=valid_indices)

    # Ensure all expected columns exist (fill NaN with 0 if missing)
    expected_cols = ['MolWt', 'LogP', 'NumHDonors', 'NumHAcceptors', 'TPSA',
                     'NumRotatableBonds', 'NumAromaticRings', 'NumAliphaticRings',
                     'charge_density', 'cavity_volume']
    for col in expected_cols:
        if col not in desc_df.columns:
            desc_df[col] = 0.0

    # Reindex to match original df (fill missing with 0)
    desc_df = desc_df.reindex(df.index).fillna(0)

    # Store fingerprints in a separate column (as object type for list/array)
    # We will save them as pickle strings or a separate file if needed,
    # but for this CSV output, we store the fingerprint as a string or object.
    # To keep the CSV clean, we might just store the first few bits or a hash,
    # but the requirement says "Generate ECFP fingerprints".
    # We will store the fingerprint as a list of integers in a JSON-like string or object.
    # For CSV compatibility, we can store as a space-separated string.
    fingerprint_strings = []
    for fp in fingerprints_list:
        # Convert numpy array to list of integers
        fp_list = fp.tolist()
        fingerprint_strings.append(fp_list)

    # Create a column for fingerprints
    desc_df['ecfp_fingerprint'] = fingerprint_strings

    # Combine with original data (only keep rows that were valid)
    # We drop rows where SMILES was invalid
    result_df = pd.concat([df.loc[valid_indices].reset_index(drop=True),
                           desc_df.loc[valid_indices].reset_index(drop=True)], axis=1)

    logger.info(f"Successfully processed {len(result_df)} molecules.")
    return result_df


def run_feature_engineering_pipeline(input_path: Optional[str] = None,
                                     output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Main entry point for the feature engineering pipeline.

    Loads the processed binding data, computes descriptors, and saves the result.

    Args:
        input_path: Path to the input CSV (default: data/processed/halide_binding_data.csv).
        output_path: Path to the output CSV (default: data/processed/halide_binding_features.csv).

    Returns:
        The processed DataFrame.
    """
    if input_path is None:
        input_path = str(get_data_path() / "processed" / "halide_binding_data.csv")
    if output_path is None:
        output_path = str(get_data_path() / "processed" / "halide_binding_features.csv")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Validate required column
    if 'host_smiles' not in df.columns:
        raise ValueError("Input DataFrame must contain 'host_smiles' column.")

    # Process molecules
    df_features = process_host_molecules(df)

    if df_features.empty:
        logger.error("Feature engineering produced no output.")
        return pd.DataFrame()

    # Save to CSV
    # Note: Storing the full fingerprint array in CSV might be heavy.
    # We store it as a string representation of the list.
    logger.info(f"Saving features to {output_path}")
    df_features.to_csv(output_path, index=False)

    # Also save the fingerprint mapping as a pickle for efficient loading later
    pickle_path = str(get_data_path() / "processed" / "fingerprint_map.pkl")
    with open(pickle_path, 'wb') as f:
        # Store a mapping of index to fingerprint for quick access
        fp_map = {}
        for i, fp_list in enumerate(df_features['ecfp_fingerprint'].tolist()):
            fp_map[i] = np.array(fp_list, dtype=np.uint8)
        pickle.dump(fp_map, f)

    logger.info(f"Feature engineering complete. Output saved to {output_path}")
    return df_features


def main():
    """Main execution function."""
    try:
        run_feature_engineering_pipeline()
        logger.info("Feature engineering pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Feature engineering pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
