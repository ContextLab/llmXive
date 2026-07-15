import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Configure logger for this module
logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed Caco-2 dataset from data/processed/caco2_clean.csv.
    
    Returns:
        pd.DataFrame: DataFrame containing SMILES and logPapp columns.
    """
    root = get_project_root()
    input_path = root / "data" / "processed" / "caco2_clean.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found at {input_path}. "
                                "Run T010 (preprocessing) first.")
    
    df = pd.read_csv(input_path)
    
    required_cols = {'smiles', 'logPapp'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Processed data missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def generate_conformers(smiles_list: List[str], n_conf: int = 20) -> Tuple[List[Any], List[int]]:
    """
    Generate 3D conformer ensembles for a list of SMILES using RDKit.
    
    Args:
        smiles_list: List of SMILES strings.
        n_conf: Number of conformers to generate per molecule (default 20 per DEV-001).
    
    Returns:
        Tuple of (list of RDKit Mol objects with conformers, list of indices that failed).
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem
    
    successful_mols = []
    failed_indices = []
    
    for idx, smi in enumerate(smiles_list):
        try:
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                failed_indices.append(idx)
                continue
            
            mol = Chem.AddHs(mol)
            # Embed conformers
            params = AllChem.ETKDGv3()
            params.maxAttempts = 500
            params.numThreads = 0  # Auto-detect
            
            # Generate conformers
            ids = AllChem.EmbedMultipleConfs(mol, numConfs=n_conf, params=params)
            
            if len(ids) == 0:
                # Generation failed
                failed_indices.append(idx)
                logger.debug(f"Conformer generation failed for index {idx}: {smi[:50]}...")
                continue
            
            # Optimize geometries
            for cid in ids:
                AllChem.UFFOptimizeMolecule(mol, confId=cid)
            
            successful_mols.append(mol)
            
        except Exception as e:
            failed_indices.append(idx)
            logger.warning(f"Error processing index {idx}: {e}")
            continue
    
    logger.info(f"Generated conformers for {len(successful_mols)}/{len(smiles_list)} molecules. "
                f"Failed: {len(failed_indices)}")
    return successful_mols, failed_indices

def calculate_variance_metrics(mols: List[Any]) -> pd.DataFrame:
    """
    Calculate bond, angle, and dihedral variance metrics for a list of RDKit molecules.
    
    Args:
        mols: List of RDKit Mol objects with conformers.
    
    Returns:
        DataFrame with variance metrics.
    """
    from rdkit import Chem
    from rdkit.Chem import rdMolTransforms
    
    results = []
    
    for idx, mol in enumerate(mols):
        try:
            # Get the first conformer (or average across conformers if multiple)
            # For simplicity and consistency with T013a, we calculate variance across the ensemble
            conf = mol.GetConformer(0) 
            n_atoms = mol.GetNumAtoms()
            
            # We need to calculate variance across the ensemble of conformers
            # If only 1 conformer exists, variance is 0. 
            # We assume n_conf >= 2 for variance calculation, else 0.
            
            n_confs = mol.GetNumConformers()
            if n_confs < 2:
                bond_var = 0.0
                angle_var = 0.0
                dihedral_var = 0.0
            else:
                bond_lengths = []
                angles = []
                dihedrals = []
                
                # Identify bonds, angles, dihedrals from the molecule topology
                # Bond: all bonds in the molecule
                # Angle: all triplets of connected atoms
                # Dihedral: all quadruplets of connected atoms
                
                bonds = []
                for bond in mol.GetBonds():
                    bonds.append((bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()))
                
                # Angles: for each atom, pairs of neighbors
                atom_neighbors = {atom.GetIdx(): [] for atom in mol.GetAtoms()}
                for bond in mol.GetBonds():
                    i = bond.GetBeginAtomIdx()
                    j = bond.GetEndAtomIdx()
                    atom_neighbors[i].append(j)
                    atom_neighbors[j].append(i)
                
                angles_tuples = []
                for center, neighbors in atom_neighbors.items():
                    for i in range(len(neighbors)):
                        for j in range(i + 1, len(neighbors)):
                            angles_tuples.append((neighbors[i], center, neighbors[j]))
                
                # Dihedrals: for each bond, pairs of neighbors on each side
                dihedral_tuples = []
                for bond in mol.GetBonds():
                    i = bond.GetBeginAtomIdx()
                    j = bond.GetEndAtomIdx()
                    # Neighbors of i excluding j
                    ni = [n for n in atom_neighbors[i] if n != j]
                    # Neighbors of j excluding i
                    nj = [n for n in atom_neighbors[j] if n != i]
                    
                    for a in ni:
                        for b in nj:
                            dihedral_tuples.append((a, i, j, b))
                
                # Calculate values for each conformer
                all_bond_lens = []
                all_angles = []
                all_dihedrals = []
                
                for cid in range(n_confs):
                    conf = mol.GetConformer(cid)
                    
                    # Bond lengths
                    for (i, j) in bonds:
                        dist = conf.GetAtomPosition(i).Distance(conf.GetAtomPosition(j))
                        all_bond_lens.append(dist)
                    
                    # Angles (in radians)
                    for (a, b, c) in angles_tuples:
                        pos_a = conf.GetAtomPosition(a)
                        pos_b = conf.GetAtomPosition(b)
                        pos_c = conf.GetAtomPosition(c)
                        # Calculate angle ABC
                        v1 = pos_a - pos_b
                        v2 = pos_c - pos_b
                        norm1 = np.linalg.norm(v1)
                        norm2 = np.linalg.norm(v2)
                        if norm1 > 1e-6 and norm2 > 1e-6:
                            cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                            cos_angle = np.clip(cos_angle, -1.0, 1.0)
                            angle = np.arccos(cos_angle)
                            all_angles.append(angle)
                    
                    # Dihedrals (in radians)
                    for (a, b, c, d) in dihedral_tuples:
                        pos_a = conf.GetAtomPosition(a)
                        pos_b = conf.GetAtomPosition(b)
                        pos_c = conf.GetAtomPosition(c)
                        pos_d = conf.GetAtomPosition(d)
                        
                        try:
                            dihedral = rdMolTransforms.GetDihedralRad(conf, a, b, c, d)
                            all_dihedrals.append(dihedral)
                        except:
                            continue
                
                # Calculate variance
                if len(all_bond_lens) > 0:
                    bond_var = np.var(all_bond_lens)
                else:
                    bond_var = 0.0
                    
                if len(all_angles) > 0:
                    angle_var = np.var(all_angles)
                else:
                    angle_var = 0.0
                    
                if len(all_dihedrals) > 0:
                    dihedral_var = np.var(all_dihedrals)
                else:
                    dihedral_var = 0.0
            
            results.append({
                'bond_variance': float(bond_var),
                'angle_variance': float(angle_var),
                'dihedral_variance': float(dihedral_var)
            })
            
        except Exception as e:
            logger.error(f"Error calculating metrics for molecule {idx}: {e}")
            # Append zeros for failed molecules to maintain alignment
            results.append({
                'bond_variance': 0.0,
                'angle_variance': 0.0,
                'dihedral_variance': 0.0
            })
    
    return pd.DataFrame(results)

def process_molecules(df: pd.DataFrame, n_conf: int = 20) -> pd.DataFrame:
    """
    Process molecules: generate conformers and calculate variance metrics.
    
    Args:
        df: DataFrame with 'smiles' column.
        n_conf: Number of conformers to generate.
    
    Returns:
        DataFrame with original data plus variance metrics.
    """
    smiles_list = df['smiles'].tolist()
    
    logger.info(f"Generating conformers for {len(smiles_list)} molecules...")
    mols, failed_indices = generate_conformers(smiles_list, n_conf)
    
    logger.info(f"Calculating variance metrics for {len(mols)} successful molecules...")
    metrics_df = calculate_variance_metrics(mols)
    
    # Combine with original data
    # Note: We only keep rows that were successfully processed. 
    # The failed indices are dropped.
    successful_indices = [i for i in range(len(smiles_list)) if i not in failed_indices]
    
    if len(successful_indices) != len(metrics_df):
        raise RuntimeError("Mismatch between successful molecules and metrics count.")
    
    # Filter original df to successful indices
    result_df = df.iloc[successful_indices].reset_index(drop=True)
    
    # Add metrics
    result_df['bond_variance'] = metrics_df['bond_variance']
    result_df['angle_variance'] = metrics_df['angle_variance']
    result_df['dihedral_variance'] = metrics_df['dihedral_variance']
    
    logger.info(f"Processed {len(result_df)} molecules successfully.")
    return result_df

def flag_outliers(df: pd.DataFrame, threshold: float = 1.5) -> pd.DataFrame:
    """
    Flag outliers using the Interquartile Range (IQR) method.
    Outlier if value > Q3 + threshold * IQR or < Q1 - threshold * IQR.
    
    Args:
        df: DataFrame with variance columns.
        threshold: IQR multiplier (default 1.5).
    
    Returns:
        DataFrame with 'is_outlier' boolean column.
    """
    cols_to_check = ['bond_variance', 'angle_variance', 'dihedral_variance']
    
    outlier_flags = pd.Series(False, index=df.index)
    
    for col in cols_to_check:
        if col not in df.columns:
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_flags = outlier_flags | col_outliers
    
    df['is_outlier'] = outlier_flags
    logger.info(f"Flagged {outlier_flags.sum()} outliers using IQR method.")
    return df

def write_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the processed descriptors to a CSV file.
    
    Args:
        df: DataFrame with smiles and variance metrics.
        output_path: Path to output CSV file.
    """
    # Ensure required columns exist
    required_cols = ['smiles', 'bond_variance', 'angle_variance', 'dihedral_variance', 'is_outlier']
    if not all(col in df.columns for col in required_cols):
        missing = set(required_cols) - set(df.columns)
        raise ValueError(f"Missing required columns for output: {missing}")
    
    # Select and order columns
    output_df = df[required_cols].copy()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(output_df)} records to {output_path}")

def main():
    """Main entry point for the descriptors pipeline."""
    configure_root_logger()
    
    root = get_project_root()
    input_path = root / "data" / "processed" / "caco2_clean.csv"
    output_path = root / "data" / "processed" / "caco2_descriptors.csv"
    
    # Load data
    logger.info("Loading processed data...")
    df = load_processed_data()
    
    # Process molecules (generate conformers and calculate metrics)
    logger.info("Processing molecules...")
    df_processed = process_molecules(df, n_conf=20)
    
    # Flag outliers
    logger.info("Flagging outliers...")
    df_final = flag_outliers(df_processed)
    
    # Write output
    logger.info("Writing output...")
    write_descriptors(df_final, output_path)
    
    logger.info("Descriptors pipeline completed successfully.")

if __name__ == "__main__":
    main()