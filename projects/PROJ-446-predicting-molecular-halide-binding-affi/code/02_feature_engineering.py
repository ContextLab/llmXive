"""
Feature Engineering Module for Molecular Halide Binding Affinity Prediction.

This module generates molecular descriptors and fingerprints for host molecules
using RDKit. It computes ECFP4 fingerprints (1024‑bit), Gasteiger charge sum
(`charge_density`), and RDKit molecular volume (`cavity_volume`).

Outputs:
    - data/raw/descriptors_added.csv: DataFrame with SMILES, host identifiers,
      standardized binding data, and all descriptor columns (including
      `ecfp_0` … `ecfp_1023`).
"""

import os
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit import DataStructs

# Project utilities
from code.utils.logger import get_logger
from code.utils.config import get_data_path

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

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
        # Add explicit hydrogens – improves descriptor calculations
        mol = Chem.AddHs(mol)
        return mol
    except Exception as e:
        logger.error(f"Error parsing SMILES '{smiles}': {e}")
        return None


def calculate_charge_density(mol: Chem.Mol) -> float:
    """
    Approximate charge density as (heteroatom count) / (molecular weight).

    Args:
        mol: RDKit Mol object.

    Returns:
        Float representing the charge density proxy.
    """
    if mol is None:
        return 0.0
    try:
        heteroatom_count = sum(
            1 for atom in mol.GetAtoms() if atom.GetAtomicNum() not in (1, 6)
        )
        mol_weight = Descriptors.MolWt(mol)
        if mol_weight <= 0:
            return 0.0
        return float(heteroatom_count / mol_weight)
    except Exception as e:
        logger.warning(f"Could not calculate charge density: {e}")
        return 0.0


def calculate_cavity_volume(mol: Chem.Mol) -> float:
    """
    Approximate cavity volume using solvent‑accessible surface area (SASA).

    Args:
        mol: RDKit Mol object.

    Returns:
        Float representing the cavity volume proxy (SASA in Å²).
    """
    if mol is None:
        return 0.0
    try:
        sasa = rdMolDescriptors.CalcSASA(mol)
        return float(sasa)
    except Exception as e:
        logger.warning(f"Could not calculate cavity volume (SASA): {e}")
        return 0.0


def generate_ecfp_fingerprint(
    mol: Chem.Mol, radius: int = 2, n_bits: int = 1024
) -> np.ndarray:
    """
    Generate an ECFP4 fingerprint (Morgan) as a binary numpy array.

    Args:
        mol: RDKit Mol object.
        radius: Fingerprint radius (2 for ECFP4).
        n_bits: Length of the fingerprint vector.

    Returns:
        Numpy array of shape (n_bits,) containing 0/1 values.
    """
    if mol is None:
        return np.zeros(n_bits, dtype=np.uint8)
    try:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros((n_bits,), dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.error(f"Error generating ECFP fingerprint: {e}")
        return np.zeros(n_bits, dtype=np.uint8)


def calculate_rdkit_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """
    Compute a standard set of RDKit descriptors plus the two custom proxies.

    Args:
        mol: RDKit Mol object.

    Returns:
        Dictionary mapping descriptor names to float values.
    """
    if mol is None:
        return {}
    try:
        desc = {
            "MolWt": Descriptors.MolWt(mol),
            "LogP": Descriptors.MolLogP(mol),
            "NumHDonors": Descriptors.NumHDonors(mol),
            "NumHAcceptors": Descriptors.NumHAcceptors(mol),
            "TPSA": Descriptors.TPSA(mol),
            "NumRotatableBonds": Descriptors.NumRotatableBonds(mol),
            "NumAromaticRings": Descriptors.NumAromaticRings(mol),
            "NumAliphaticRings": Descriptors.NumAliphaticRings(mol),
            "charge_density": calculate_charge_density(mol),
            "cavity_volume": calculate_cavity_volume(mol),
        }
        return desc
    except Exception as e:
        logger.error(f"Error calculating RDKit descriptors: {e}")
        return {}


# -------------------------------------------------------------------------
# Core processing
# -------------------------------------------------------------------------

def process_host_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each host row, compute descriptors and a 1024‑bit ECFP4 fingerprint.
    The fingerprint bits are expanded into separate columns named
    ``ecfp_0`` … ``ecfp_1023``.

    The input DataFrame must contain either a ``host_smiles`` column or a
    ``smiles`` column (the latter is used by the ingestion step).

    Returns:
        DataFrame with original columns plus descriptor columns and the
        1024 fingerprint columns.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    logger.info(f"Processing {len(df)} host molecules for feature engineering...")

    # Lists to collect per‑row results
    descriptor_rows: List[Dict[str, float]] = []
    fingerprint_rows: List[np.ndarray] = []
    valid_indices: List[int] = []

    for idx, row in df.iterrows():
        # Accept either 'host_smiles' or 'smiles'
        smiles = row.get("host_smiles") or row.get("smiles")
        if pd.isna(smiles):
            logger.warning(f"Row {idx} missing SMILES, skipping.")
            continue

        mol = parse_smiles_to_mol(smiles)
        if mol is None:
            logger.warning(f"Row {idx} has invalid SMILES, skipping.")
            continue

        # Compute descriptors and fingerprint
        desc = calculate_rdkit_descriptors(mol)
        fp = generate_ecfp_fingerprint(mol, radius=2, n_bits=1024)

        descriptor_rows.append(desc)
        fingerprint_rows.append(fp)
        valid_indices.append(idx)

    if not descriptor_rows:
        logger.warning("No valid molecules were processed; returning empty DataFrame with descriptor columns.")
        # Build an empty DataFrame that contains the expected descriptor and fingerprint columns
        # Descriptor columns come from calculate_rdkit_descriptors on a dummy molecule
        dummy_mol = Chem.MolFromSmiles("C")  # methane
        dummy_desc = calculate_rdkit_descriptors(dummy_mol)
        descriptor_cols = list(dummy_desc.keys())
        fp_cols = [f"ecfp_{i}" for i in range(1024)]
        empty_cols = list(df.columns) + descriptor_cols + fp_cols
        return pd.DataFrame(columns=empty_cols)

    # Descriptor DataFrame (indexed by original row index)
    desc_df = pd.DataFrame(descriptor_rows, index=valid_indices)

    # Fingerprint DataFrame – one column per bit
    fp_array = np.vstack(fingerprint_rows)  # shape (n_valid, 1024)
    fp_columns = [f"ecfp_{i}" for i in range(fp_array.shape[1])]
    fp_df = pd.DataFrame(fp_array, index=valid_indices, columns=fp_columns)

    # Combine descriptors, fingerprints, and the original rows that were valid
    original_valid = df.loc[valid_indices].reset_index(drop=True)
    combined = pd.concat(
        [original_valid.reset_index(drop=True), desc_df.reset_index(drop=True), fp_df.reset_index(drop=True)],
        axis=1,
    )

    logger.info(f"Successfully processed {len(combined)} molecules.")
    return combined


def run_feature_engineering_pipeline(
    input_path: Optional[str] = None, output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Entry point for the feature‑engineering stage.

    - Loads the cleaned host CSV (produced by the ingestion step).
    - Computes descriptors and a 1024‑bit ECFP4 fingerprint.
    - Writes the enriched table to ``data/raw/descriptors_added.csv``.
    - Also persists a pickle mapping of row index → fingerprint array for
      downstream fast loading.

    Args:
        input_path: Optional explicit path to the cleaned CSV.
        output_path: Optional explicit path for the enriched CSV.

    Returns:
        The enriched DataFrame.
    """
    # Default locations (relative to the project root)
    if input_path is None:
        # Primary expectation: cleaned hosts from ingestion
        input_path = str(get_data_path() / "raw" / "filtered_hosts.csv")
    if output_path is None:
        output_path = str(get_data_path() / "raw" / "descriptors_added.csv")

    # Ensure the output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Resolve input file – do NOT fall back to simulated data.
    # -----------------------------------------------------------------
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Expected input file not found: {input_path}")

    logger.info(f"Loading cleaned host data from {input_path}")
    df = pd.read_csv(input_path)

    # Verify we have a SMILES column (the ingestion step uses 'smiles')
    if "smiles" not in df.columns and "host_smiles" not in df.columns:
        raise ValueError("Input CSV must contain a 'smiles' or 'host_smiles' column.")

    df_features = process_host_molecules(df)

    if df_features.empty:
        logger.info("Feature engineering produced an empty DataFrame (no valid molecules).")
    else:
        logger.info(f"Feature engineering produced {len(df_features)} rows.")

    # Save the enriched CSV
    logger.info(f"Saving enriched descriptors to {output_path}")
    df_features.to_csv(output_path, index=False)

    # Persist fingerprint map for quick loading by downstream scripts
    fingerprint_pickle = str(get_data_path() / "raw" / "fingerprint_map.pkl")
    logger.info(f"Saving fingerprint map to {fingerprint_pickle}")
    fp_columns = [col for col in df_features.columns if col.startswith("ecfp_")]
    fp_map = {
        idx: np.array(row, dtype=np.uint8)
        for idx, row in enumerate(df_features[fp_columns].values)
    }
    with open(fingerprint_pickle, "wb") as f:
        pickle.dump(fp_map, f)

    logger.info("Feature engineering pipeline completed successfully.")
    return df_features


def main() -> None:
    """CLI entry point."""
    try:
        run_feature_engineering_pipeline()
        logger.info("Feature engineering completed without errors.")
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        raise


if __name__ == "__main__":
    main()
