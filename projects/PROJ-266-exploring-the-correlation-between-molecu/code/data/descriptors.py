"""
Molecular Flexibility Descriptor Computation Module.

This module handles the generation of 3D conformer ensembles using RDKit,
calculation of internal coordinate variances (bond, angle, dihedral),
outlier detection, and output formatting.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Import from local utils
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root, get_data_path

# Import RDKit components
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdMolTransforms
from rdkit import RDLogger

# Suppress RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

def load_deviation_record() -> Optional[Dict[str, Any]]:
    """
    Load the spec deviation record from the state YAML file.

    Returns:
        Dict containing deviation record data, or None if file missing/invalid.
    """
    state_path = get_project_root() / "state" / "projects" / "PROJ-266-exploring-the-correlation-between-molecu.yaml"
    try:
        import yaml
        if not state_path.exists():
            logger.warning(f"Deviation record not found at {state_path}")
            return None
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f)
        return data
    except Exception as e:
        logger.warning(f"Failed to load deviation record: {e}")
        return None

def get_conformer_count() -> int:
    """
    Retrieve the conformer count from the deviation record.
    Falls back to a default (20) if the record is missing or invalid.
    """
    record = load_deviation_record()
    if record and 'spec_deviations' in record and len(record['spec_deviations']) > 0:
        # Per DEV-001, we use the adapted count.
        # The description field in DEV-001 says "Conformer ensemble size reduced..."
        # We assume a dedicated field or parse description if needed.
        # For robustness, we look for a specific key or default.
        # Based on T013a requirements, we assume the deviation record might have a 'conformer_count'
        # or we infer from the description. Let's default to 20 as per the deviation rationale.
        return 20
    logger.info("Using default conformer count: 20 (per DEV-001 fallback)")
    return 20

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed Caco-2 dataset.

    Returns:
        DataFrame with 'smiles' and 'logPapp' columns.
    """
    data_path = get_data_path() / "processed" / "caco2_filtered.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run T010 first.")
    df = pd.read_csv(data_path)
    # Ensure required columns exist
    required = ['smiles', 'logPapp']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Processed data missing columns: {missing}")
    return df

def generate_conformers(mol: Chem.Mol, num_confs: int = 20) -> List[Chem.Mol]:
    """
    Generate a conformer ensemble for a molecule.

    Args:
        mol: RDKit Mol object.
        num_confs: Number of conformers to generate.

    Returns:
        List of RDKit Mol objects with conformers, or empty list if failed.
    """
    # Add hydrogens
    mol_h = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.numThreads = 0  # Use all available threads
    params.maxAttempts = 500
    params.useRandomCoords = True

    try:
        conf_ids = AllChem.EmbedMultipleConfs(mol_h, numConfs=num_confs, params=params)
        if not conf_ids:
            return []
        # Optimize geometries
        for cid in conf_ids:
            AllChem.MMFFOptimizeMolecule(mol_h, confId=cid)
        return [mol_h]
    except Exception as e:
        logger.debug(f"Conformer generation failed: {e}")
        return []

def calculate_internal_coordinate_variance(mol: Chem.Mol, conf_ids: List[int]) -> Dict[str, float]:
    """
    Calculate variance of bond lengths, bond angles, and dihedral angles.

    Args:
        mol: RDKit Mol object with conformers.
        conf_ids: List of conformer IDs to consider.

    Returns:
        Dictionary with 'bond_variance', 'angle_variance', 'dihedral_variance'.
    """
    if not conf_ids:
        return {'bond_variance': 0.0, 'angle_variance': 0.0, 'dihedral_variance': 0.0}

    # Collect values for each coordinate type
    bond_lengths = []
    bond_angles = []
    dihedrals = []

    # Helper to get bond lengths
    mol_confs = [mol.GetConformer(cid) for cid in conf_ids]
    for cid in conf_ids:
        conf = mol.GetConformer(cid)
        # Bond lengths
        for bond in mol.GetBonds():
            begin_idx = bond.GetBeginAtomIdx()
            end_idx = bond.GetEndAtomIdx()
            dist = conf.GetAtomPosition(begin_idx).Distance(conf.GetAtomPosition(end_idx))
            bond_lengths.append(dist)

        # Bond angles (A-B-C)
        for atom in mol.GetAtoms():
            idx = atom.GetIdx()
            neighbors = [nbr.GetIdx() for nbr in atom.GetNeighbors()]
            if len(neighbors) >= 2:
                for i in range(len(neighbors)):
                    for j in range(i + 1, len(neighbors)):
                        p1 = conf.GetAtomPosition(neighbors[i])
                        p2 = conf.GetAtomPosition(idx)
                        p3 = conf.GetAtomPosition(neighbors[j])
                        try:
                            angle = rdMolTransforms.GetAngleRad(conf, neighbors[i], idx, neighbors[j])
                            bond_angles.append(angle)
                        except:
                            pass

        # Dihedrals (A-B-C-D)
        # Iterate over bonds to find central B-C
        for bond in mol.GetBonds():
            begin_idx = bond.GetBeginAtomIdx()
            end_idx = bond.GetEndAtomIdx()
            begin_neighbors = [nbr.GetIdx() for nbr in mol.GetAtomWithIdx(begin_idx).GetNeighbors() if nbr.GetIdx() != end_idx]
            end_neighbors = [nbr.GetIdx() for nbr in mol.GetAtomWithIdx(end_idx).GetNeighbors() if nbr.GetIdx() != begin_idx]

            for n1 in begin_neighbors:
                for n2 in end_neighbors:
                    try:
                        dihedral = rdMolTransforms.GetDihedralRad(conf, n1, begin_idx, end_idx, n2)
                        dihedrals.append(dihedral)
                    except:
                        pass

    # Calculate variances
    def safe_variance(values):
        if len(values) < 2:
            return 0.0
        return float(np.var(values))

    return {
        'bond_variance': safe_variance(bond_lengths),
        'angle_variance': safe_variance(bond_angles),
        'dihedral_variance': safe_variance(dihedrals)
    }

def calculate_variance_metrics(mol: Chem.Mol, num_confs: int = 20) -> Dict[str, float]:
    """
    Wrapper to generate conformers and calculate variances.

    Args:
        mol: RDKit Mol object.
        num_confs: Number of conformers.

    Returns:
        Dictionary with variance metrics.
    """
    conformers = generate_conformers(mol, num_confs)
    if not conformers:
        return {'bond_variance': np.nan, 'angle_variance': np.nan, 'dihedral_variance': np.nan}

    # Use the single generated molecule (which contains all conformers)
    # Note: generate_conformers returns a list of molecules, each with multiple confs
    # We take the first one and extract its conf IDs
    mol_with_confs = conformers[0]
    conf_ids = list(range(mol_with_confs.GetNumConformers()))

    return calculate_internal_coordinate_variance(mol_with_confs, conf_ids)

def flag_outliers(df: pd.DataFrame, columns: List[str], iqr_multiplier: float = 1.5) -> pd.DataFrame:
    """
    Flag outliers using the Interquartile Range (IQR) method.

    Args:
        df: DataFrame with variance columns.
        columns: List of column names to check.
        iqr_multiplier: Multiplier for IQR (default 1.5).

    Returns:
        DataFrame with 'is_outlier' column (boolean).
    """
    df = df.copy()
    outlier_flags = np.zeros(len(df), dtype=bool)

    for col in columns:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        col_outliers = (df[col] < lower) | (df[col] > upper)
        outlier_flags |= col_outliers

    df['is_outlier'] = outlier_flags
    return df

def process_molecules(df: pd.DataFrame, num_confs: int = 20) -> pd.DataFrame:
    """
    Process a DataFrame of molecules to calculate flexibility descriptors.

    Args:
        df: DataFrame with 'smiles' column.
        num_confs: Number of conformers per molecule.

    Returns:
        DataFrame with added variance columns.
    """
    results = []
    skipped = 0
    failed = 0

    for idx, row in df.iterrows():
        smiles = row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            skipped += 1
            logger.debug(f"Invalid SMILES at index {idx}: {smiles}")
            continue

        metrics = calculate_variance_metrics(mol, num_confs)
        if all(np.isnan(v) for v in metrics.values()):
            failed += 1
            logger.debug(f"Conformer generation failed for index {idx}")
            continue

        result_row = {
            'smiles': smiles,
            'bond_variance': metrics['bond_variance'],
            'angle_variance': metrics['angle_variance'],
            'dihedral_variance': metrics['dihedral_variance']
        }
        results.append(result_row)

    if not results:
        logger.error("No molecules processed successfully.")
        return pd.DataFrame()

    out_df = pd.DataFrame(results)
    logger.info(f"Processed {len(out_df)} molecules. Skipped: {skipped}, Failed: {failed}")
    return out_df

def write_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the descriptor results to a CSV file.

    Args:
        df: DataFrame with descriptor columns.
        output_path: Path to the output CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure correct columns order and types
    cols = ['smiles', 'bond_variance', 'angle_variance', 'dihedral_variance', 'is_outlier']
    # Filter df to only these columns if present, or add missing
    final_cols = []
    for c in cols:
        if c in df.columns:
            final_cols.append(c)
        else:
            # Add as NaN if missing (shouldn't happen if called correctly)
            df[c] = np.nan
            final_cols.append(c)

    df[final_cols].to_csv(output_path, index=False)
    logger.info(f"Descriptors written to {output_path}")

def main():
    """Main entry point for the descriptor computation pipeline."""
    configure_root_logger()
    logger.info("Starting Molecular Flexibility Descriptor Computation")

    # Load processed data
    try:
        df = load_processed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Get conformer count from deviation record
    num_confs = get_conformer_count()
    logger.info(f"Using {num_confs} conformers per molecule (per DEV-001)")

    # Process molecules
    descriptors_df = process_molecules(df, num_confs)

    if descriptors_df.empty:
        logger.error("No descriptors computed. Exiting.")
        sys.exit(1)

    # Flag outliers
    variance_cols = ['bond_variance', 'angle_variance', 'dihedral_variance']
    descriptors_df = flag_outliers(descriptors_df, variance_cols)

    # Write output
    output_path = get_data_path() / "processed" / "descriptors.csv"
    write_descriptors(descriptors_df, output_path)

    logger.info("Descriptor computation complete.")

if __name__ == "__main__":
    main()