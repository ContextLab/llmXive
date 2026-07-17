"""
Molecular Flexibility Descriptor Computation Module.

This module handles the generation of 3D conformer ensembles and the calculation
of internal coordinate variances (bond, angle, dihedral) as flexibility descriptors.
It adheres to Deviation ID DEV-001 (Plan.md) which overrides Spec FR-003,
limiting conformer generation to 20 per molecule for CPU feasibility.

Primary Output: Dihedral Variance (rad^2)
Secondary Outputs: Bond Variance, Angle Variance, Outlier Flags
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Local imports matching API surface
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root, set_seed

# RDKit imports
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from rdkit import RDLogger
except ImportError:
    raise ImportError("RDKit is required for this module. Install via: pip install rdkit")

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

# Constants
CONFORMER_COUNT = 20  # Per DEV-001 (overriding Spec FR-003's 50)
RANDOM_SEED = 42

def load_processed_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the preprocessed Caco-2 dataset from the processed data directory.

    Args:
        filepath: Optional specific path. If None, uses default project path.

    Returns:
        DataFrame with 'smiles' and 'logPapp' columns.
    """
    if filepath is None:
        project_root = get_project_root()
        filepath = project_root / "data" / "processed" / "caco2_cleaned.csv"

    if not filepath.exists():
        raise FileNotFoundError(f"Processed data not found at {filepath}. "
                                "Run code/data/preprocessing.py first.")

    logger.info(f"Loading processed data from {filepath}")
    df = pd.read_csv(filepath)

    required_cols = ['smiles', 'logPapp']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Processed data missing required columns: {missing}")

    # Filter for non-null SMILES and logPapp again just in case
    df = df.dropna(subset=required_cols)
    logger.info(f"Loaded {len(df)} valid records.")
    return df


def generate_conformers(smiles: str, n_conformers: int = CONFORMER_COUNT) -> Optional[List[Chem.Mol]]:
    """
    Generate 3D conformer ensemble for a single molecule.

    Implements DEV-001: Uses 20 conformers instead of 50 for CPU feasibility.

    Args:
        smiles: SMILES string of the molecule.
        n_conformers: Number of conformers to generate.

    Returns:
        List of RDKit Mol objects with 3D coordinates, or None if generation fails.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Could not parse SMILES: {smiles}")
        return None

    # Add hydrogens
    mol_h = Chem.AddHs(mol)

    # Embed conformers
    # Using ETKDGv3 for better geometric accuracy
    params = AllChem.ETKDGv3()
    params.randomSeed = RANDOM_SEED
    params.maxAttempts = 500
    params.numThreads = 1  # Force single thread for reproducibility in CI

    try:
        # Attempt embedding
        ids = AllChem.EmbedMultipleConfs(mol_h, numConfs=n_conformers, params=params)
        if not ids:
            logger.warning(f"No conformers generated for {smiles}.")
            return None

        # Optimize geometry for each conformer
        # We do this for all, but if it's too slow, we could limit.
        # For 20 conformers, it's usually fast enough.
        for cid in ids:
            try:
                AllChem.MMFFOptimizeMoleculeConfs(mol_h, confId=cid)
            except Exception:
                # MMFF might fail for some weird structures, skip optimization for that conf
                pass

        return [mol_h]
    except Exception as e:
        logger.warning(f"Conformer generation failed for {smiles}: {e}")
        return None


def calculate_variance_metrics(mol: Chem.Mol) -> Dict[str, float]:
    """
    Calculate internal coordinate variances (bond, angle, dihedral) from the conformer ensemble.

    Returns a dictionary with:
      - bond_variance (rad^2 or dimensionless)
      - angle_variance (rad^2)
      - dihedral_variance (rad^2) - PRIMARY descriptor

    Args:
        mol: RDKit Mol object with multiple conformers.

    Returns:
        Dictionary of variance metrics.
    """
    confs = [mol.GetConformer(i) for i in range(mol.GetNumConformers())]
    if not confs:
        return {"bond_variance": np.nan, "angle_variance": np.nan, "dihedral_variance": np.nan}

    # We need to collect values across conformers for specific internal coordinates.
    # To make this robust and comparable across molecules, we focus on:
    # 1. Bonds: Lengths of all bonds.
    # 2. Angles: Angles of all triplets (i-j-k).
    # 3. Dihedrals: Dihedrals of all quadruplets (i-j-k-l).
    # However, calculating ALL for large molecules is expensive and the "set" of
    # coordinates changes with molecule size.
    # Strategy:
    # - Bonds: Calculate variance of ALL bond lengths in the ensemble.
    # - Angles: Calculate variance of ALL bond angles.
    # - Dihedrals: Calculate variance of ALL dihedral angles.
    # Then take the mean of these variances? Or the variance of the flattened list?
    # The spec asks for "torsional variance" as a single metric.
    # Interpretation: Variance of the distribution of all dihedral angles observed
    # across all conformers and all rotatable bonds.

    bond_lengths = []
    bond_angles = []
    dihedral_angles = []

    # Helper to get atom indices
    atoms = mol.GetAtoms()
    num_atoms = mol.GetNumAtoms()

    # We need to map indices consistently across conformers.
    # RDKit Mol keeps atom order consistent.

    # 1. Bonds
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        for conf in confs:
            p1 = conf.GetAtomPosition(i)
            p2 = conf.GetAtomPosition(j)
            dist = np.sqrt(np.sum((np.array(p1) - np.array(p2))**2))
            bond_lengths.append(dist)

    # 2. Angles (i-j-k)
    # Iterate over all atoms j, and their neighbors i, k
    for atom in mol.GetAtoms():
        j_idx = atom.GetIdx()
        neighbors = [a.GetIdx() for a in atom.GetNeighbors()]
        if len(neighbors) < 2:
            continue
        # All pairs of neighbors
        for i_idx in neighbors:
            for k_idx in neighbors:
                if i_idx >= k_idx:
                    continue
                # Angle i-j-k
                for conf in confs:
                    p_i = conf.GetAtomPosition(i_idx)
                    p_j = conf.GetAtomPosition(j_idx)
                    p_k = conf.GetAtomPosition(k_idx)

                    v1 = np.array(p_i) - np.array(p_j)
                    v2 = np.array(p_k) - np.array(p_j)

                    # Normalize
                    v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
                    v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)

                    dot = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
                    angle = np.arccos(dot)
                    bond_angles.append(angle)

    # 3. Dihedrals (i-j-k-l)
    # Focus on rotatable bonds? Or all dihedrals?
    # Spec FR-004 implies "torsional variance". Usually implies rotatable bonds.
    # Let's calculate dihedrals for all 4-atom chains to capture global flexibility,
    # but specifically prioritize rotatable bonds if possible.
    # For simplicity and robustness across diverse molecules, we calculate all unique dihedrals.
    # This is O(N^4) worst case, but N is small for drug-like molecules.
    # Optimization: Only consider dihedrals involving at least one rotatable bond?
    # Let's stick to all unique dihedrals formed by connected atoms (i-j-k-l).

    # Get all bonds
    bonds = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) for b in mol.GetBonds()]
    bond_set = set(bonds)
    bond_set.update([(b[1], b[0]) for b in bonds])

    # Find all paths of length 3 (4 atoms)
    for j_idx in range(num_atoms):
        neighbors_j = [a.GetIdx() for a in mol.GetAtomWithIdx(j_idx).GetNeighbors()]
        for k_idx in neighbors_j:
            neighbors_k = [a.GetIdx() for a in mol.GetAtomWithIdx(k_idx).GetNeighbors()]
            for i_idx in neighbors_j:
                if i_idx == k_idx: continue
                for l_idx in neighbors_k:
                    if l_idx == j_idx: continue
                    # Ensure unique set (i, j, k, l) vs (l, k, j, i)
                    # We can enforce i < l to avoid duplicates if the graph is symmetric,
                    # but let's just collect and maybe dedup later if needed.
                    # Actually, i-j-k-l and l-k-j-i are the same dihedral magnitude.
                    # Let's just collect all and let variance handle it (symmetry cancels out).
                    # But to reduce noise, let's enforce i < l.
                    if i_idx > l_idx: continue

                    for conf in confs:
                        p_i = conf.GetAtomPosition(i_idx)
                        p_j = conf.GetAtomPosition(j_idx)
                        p_k = conf.GetAtomPosition(k_idx)
                        p_l = conf.GetAtomPosition(l_idx)

                        v1 = np.array(p_i) - np.array(p_j)
                        v2 = np.array(p_k) - np.array(p_j)
                        v3 = np.array(p_l) - np.array(p_k)

                        # Dihedral calculation
                        n1 = np.cross(v1, v2)
                        n2 = np.cross(v2, v3)

                        n1 /= np.linalg.norm(n1) + 1e-8
                        n2 /= np.linalg.norm(n2) + 1e-8

                        m1 = np.cross(n1, v2 / (np.linalg.norm(v2) + 1e-8))

                        x = np.dot(n1, n2)
                        y = np.dot(m1, n2)

                        dihedral = np.arctan2(y, x)
                        dihedral_angles.append(dihedral)

    # Calculate variances
    # Use np.var with ddof=1 for sample variance
    def safe_var(lst):
        if not lst or len(lst) < 2:
            return np.nan
        return float(np.var(lst, ddof=1))

    return {
        "bond_variance": safe_var(bond_lengths),
        "angle_variance": safe_var(bond_angles),
        "dihedral_variance": safe_var(dihedral_angles)
    }


def flag_outliers(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Flag outliers using the Interquartile Range (IQR) method.
    Condition: Value > Q3 + 1.5*IQR or Value < Q1 - 1.5*IQR.

    Args:
        df: DataFrame with variance columns.
        columns: List of columns to check. Defaults to variance columns.

    Returns:
        DataFrame with 'is_outlier' boolean column.
    """
    if columns is None:
        columns = ['bond_variance', 'angle_variance', 'dihedral_variance']

    # Ensure columns exist
    valid_cols = [c for c in columns if c in df.columns]
    if not valid_cols:
        logger.warning("No variance columns found for outlier detection.")
        df['is_outlier'] = False
        return df

    outlier_mask = pd.Series([False] * len(df), index=df.index)

    for col in valid_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_mask = outlier_mask | col_outliers

    df['is_outlier'] = outlier_mask
    return df


def process_molecules(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process a DataFrame of molecules: generate conformers and calculate metrics.

    Args:
        df: DataFrame with 'smiles' column.

    Returns:
        List of dictionaries containing smiles and calculated metrics.
    """
    results = []
    total = len(df)
    processed = 0
    failed = 0

    # Set seed for reproducibility in sampling if needed later
    set_seed(RANDOM_SEED)

    for idx, row in df.iterrows():
        smiles = row['smiles']
        # Optional: logPapp for later correlation, but not needed for descriptor calc
        logpapp = row.get('logPapp', None)

        conformers = generate_conformers(smiles)

        if conformers is None:
            failed += 1
            # Log failure (T013c requirement)
            logger.debug(f"Skipping {smiles}: Conformer generation failed.")
            continue

        # Calculate metrics
        metrics = calculate_variance_metrics(conformers[0]) # List contains one mol with multiple confs

        # Add original data
        metrics['smiles'] = smiles
        if logpapp is not None:
            metrics['logPapp'] = logpapp

        results.append(metrics)
        processed += 1

        if processed % 50 == 0:
            logger.info(f"Processed {processed}/{total} molecules...")

    if processed == 0:
        raise RuntimeError("No molecules were successfully processed.")

    logger.info(f"Successfully processed {processed} molecules. Failed: {failed}.")
    return results


def write_descriptors(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the computed descriptors to a CSV file.

    Output columns: smiles, bond_variance, angle_variance, dihedral_variance, is_outlier
    (is_outlier is added after this function in the main flow, or we can do it here if we pass df)

    Args:
        results: List of result dictionaries.
        output_path: Path to save the CSV.
    """
    if not results:
        raise ValueError("No results to write.")

    df = pd.DataFrame(results)

    # Ensure column order and types
    # We calculate outliers in the main function after this, or we can do it here.
    # The task T014c says "Implement output formatting... to save results".
    # It lists 'is_outlier' as a required column.
    # So we must flag outliers before writing.
    # But flag_outliers needs a DataFrame.
    # So we do it here.

    df = flag_outliers(df)

    # Select and order columns
    output_cols = ['smiles', 'bond_variance', 'angle_variance', 'dihedral_variance', 'is_outlier']
    # Add logPapp if present (for downstream analysis)
    if 'logPapp' in df.columns:
        output_cols.append('logPapp')

    df = df[output_cols]

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved to {output_path}")
    logger.info(f"Total records: {len(df)}, Outliers: {df['is_outlier'].sum()}")


def main():
    """
    Main entry point for the descriptor generation pipeline.
    1. Load processed data.
    2. Generate conformers.
    3. Calculate variances.
    4. Flag outliers.
    5. Save to CSV.
    """
    configure_root_logger()
    project_root = get_project_root()

    input_path = project_root / "data" / "processed" / "caco2_cleaned.csv"
    output_path = project_root / "data" / "processed" / "descriptors.csv"

    logger.info("Starting Molecular Flexibility Descriptor Pipeline.")

    try:
        # Load data
        df = load_processed_data(input_path)

        # Process
        results = process_molecules(df)

        # Write output (includes outlier flagging)
        write_descriptors(results, output_path)

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()