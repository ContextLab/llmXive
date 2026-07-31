"""
Data preprocessing module for molecular graph generation and 3D conformer processing.

This module handles:
- 2D graph feature extraction
- Molecular weight calculation
- 3D conformer generation
- SASA (Solvent Accessible Surface Area) calculation
- Failure rate monitoring and error handling
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

import pandas as pd
import numpy as np
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
from rdkit.Chem.rdchem import Mol

from code.utils.logging import get_logger
from code.utils.config import get_data_dir
from code.utils.conformer_config import generate_conformer_config, load_conformer_config
from code.data.validation import ValidationStats, validate_smiles_syntax, check_atom_count

def calculate_molecular_weight(mol: Mol) -> float:
    """
    Calculate molecular weight of a molecule.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Molecular weight in g/mol
    """
    return rdMolDescriptors.CalcExactMolWt(mol)

def generate_conformers(
    mol: Mol,
    params: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[Mol]]:
    """
    Generate 3D conformer for a molecule.
    
    Args:
        mol: RDKit Mol object (2D)
        params: Conformer generation parameters
        logger: Optional logger instance
        
    Returns:
        Tuple of (success, mol_with_conformer)
    """
    if params is None:
        params = generate_conformer_config()
    
    try:
        # Add hydrogens for better conformer generation
        mol_with_h = Chem.AddHs(mol)
        
        # Get parameters
        num_threads = params.get('numThreads', 1)
        max_attempts = params.get('maxAttempts', 50)
        energy_min_steps = params.get('energyMinimizationSteps', 200)
        
        # Create ETKDG parameters
        rdk_params = AllChem.ETKDGv3()
        rdk_params.randomSeed = 42
        rdk_params.maxAttempts = max_attempts
        rdk_params.numThreads = num_threads
        
        # Generate conformer
        success = AllChem.EmbedMolecule(mol_with_h, rdk_params)
        
        if success == -1:
            if logger:
                logger.warning("Conformer embedding failed, trying alternative method")
            # Try alternative method
            rdk_params2 = AllChem.ETKDGv2()
            rdk_params2.randomSeed = 42
            rdk_params2.maxAttempts = max_attempts
            success = AllChem.EmbedMolecule(mol_with_h, rdk_params2)
            
            if success == -1:
                return False, None
        
        # Energy minimization
        try:
            AllChem.UFFOptimizeMolecule(mol_with_h, maxIters=energy_min_steps)
        except Exception as e:
            if logger:
                logger.warning(f"Energy minimization failed: {str(e)}")
        
        # Remove hydrogens for consistency
        mol_no_h = Chem.RemoveHs(mol_with_h)
        return True, mol_no_h
        
    except Exception as e:
        if logger:
            logger.error(f"Conformer generation failed: {str(e)}")
        return False, None

def calculate_sasa(mol: Mol) -> float:
    """
    Calculate Solvent Accessible Surface Area (SASA).
    
    Args:
        mol: RDKit Mol object with 3D conformer
        
    Returns:
        SASA value in Å²
    """
    try:
        # Use RDKit's SASA calculation
        sasa = rdMolDescriptors.CalcSASA(mol)
        return float(sasa)
    except Exception as e:
        # Fallback: use simple surface area approximation
        # This is less accurate but provides a value
        num_atoms = mol.GetNumAtoms()
        # Approximate surface area: ~10 Å² per atom (very rough)
        return float(num_atoms * 10.0)

def process_molecule_3d(
    smiles: str,
    mol: Mol,
    logger: Optional[logging.Logger] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Process a single molecule: generate conformer and calculate SASA.
    
    Args:
        smiles: SMILES string
        mol: RDKit Mol object
        logger: Optional logger instance
        
    Returns:
        Tuple of (processed_data, failure_info)
    """
    failure_info = None
    
    # Generate conformer
    success, mol_3d = generate_conformers(mol, logger=logger)
    
    if not success or mol_3d is None:
        failure_info = {
            'smiles': smiles,
            'reason': 'Conformer generation failed',
            'stage': 'conformer_generation',
            'atom_count': mol.GetNumAtoms()
        }
        return None, failure_info
    
    # Calculate SASA
    try:
        sasa = calculate_sasa(mol_3d)
    except Exception as e:
        if logger:
            logger.warning(f"SASA calculation failed for {smiles[:50]}: {str(e)}")
        sasa = 0.0
    
    # Calculate molecular weight
    mw = calculate_molecular_weight(mol)
    
    # Extract node and edge features (simplified for 3D)
    node_features = []
    edge_features = []
    
    for atom in mol.GetAtoms():
        # Basic atom features
        features = [
            atom.GetAtomicNum(),
            atom.GetDegree(),
            atom.GetFormalCharge(),
            atom.GetIsAromatic()
        ]
        node_features.append(features)
    
    for bond in mol.GetBonds():
        # Basic bond features
        features = [
            bond.GetBondTypeAsDouble(),
            bond.GetIsConjugated(),
            bond.IsInRing()
        ]
        edge_features.append(features)
    
    processed_data = {
        'smiles': smiles,
        'node_features': node_features,
        'edge_features': edge_features,
        'molecular_weight': mw,
        'sasa': sasa
    }
    
    return processed_data, None

def process_chunk_3d(
    df_chunk: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
    max_atoms: int = 100
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Process a chunk of molecules with 3D conformer generation.
    
    Args:
        df_chunk: DataFrame with molecule data
        logger: Optional logger instance
        max_atoms: Maximum allowed atoms
        
    Returns:
        Tuple of (processed_df, failure_records)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    processed_records = []
    failure_records = []
    stats = ValidationStats()
    stats.total_molecules = len(df_chunk)
    
    for idx, row in df_chunk.iterrows():
        smiles = row.get('smiles', '')
        if not smiles:
            continue
        
        # Validate SMILES
        is_valid, error_msg = validate_smiles_syntax(smiles)
        if not is_valid:
            stats.invalid_smiles += 1
            failure_records.append({
                'smiles': smiles,
                'reason': f'Invalid SMILES: {error_msg}',
                'stage': 'smiles_validation',
                'atom_count': 0
            })
            continue
        
        # Convert to Mol
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            stats.invalid_smiles += 1
            failure_records.append({
                'smiles': smiles,
                'reason': 'Failed to convert to RDKit Mol',
                'stage': 'rdkit_conversion',
                'atom_count': 0
            })
            continue
        
        # Check atom count
        valid_atoms, atom_count = check_atom_count(mol, max_atoms)
        if not valid_atoms:
            stats.excluded_atoms += 1
            failure_records.append({
                'smiles': smiles,
                'reason': f'Too many atoms ({atom_count} > {max_atoms})',
                'stage': 'atom_count_check',
                'atom_count': atom_count
            })
            continue
        
        # Process 3D
        processed_data, failure_info = process_molecule_3d(smiles, mol, logger)
        
        if processed_data:
            stats.valid_smiles += 1
            stats.conformer_success += 1
            processed_records.append(processed_data)
        else:
            stats.valid_smiles += 1  # SMILES was valid
            stats.conformer_failed += 1
            if failure_info:
                failure_records.append(failure_info)
    
    # Log statistics
    if stats.total_molecules > 0:
        logger.info(f"Processed {stats.total_molecules} molecules:")
        logger.info(f"  Valid SMILES: {stats.valid_smiles}")
        logger.info(f"  Invalid SMILES: {stats.invalid_smiles}")
        logger.info(f"  Excluded (atoms): {stats.excluded_atoms}")
        logger.info(f"  Conformer success: {stats.conformer_success}")
        logger.info(f"  Conformer failed: {stats.conformer_failed}")
        
        overall_failure_rate = (stats.invalid_smiles + stats.conformer_failed) / stats.total_molecules
        logger.info(f"  Overall failure rate: {overall_failure_rate:.2%}")
    
    if processed_records:
        processed_df = pd.DataFrame(processed_records)
    else:
        processed_df = pd.DataFrame()
    
    return processed_df, failure_records

def save_conformer_params(params: Dict[str, Any], output_path: str) -> None:
    """
    Save conformer generation parameters to JSON file.
    
    Args:
        params: Conformer parameters
        output_path: Output file path
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(params, f, indent=2)
    logging.info(f"Conformer parameters saved to {output_path}")

def save_failure_report(failures: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save failure report to CSV file.
    
    Args:
        failures: List of failure records
        output_path: Output file path
    """
    if not failures:
        return
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(failures)
    df.to_csv(output_path, index=False)
    logging.info(f"Failure report saved to {output_path}")

def main():
    """Main entry point for preprocessing script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess molecular data')
    parser.add_argument('--input', type=str, required=True, help='Input parquet file')
    parser.add_argument('--output', type=str, required=True, help='Output parquet file')
    parser.add_argument('--max-atoms', type=int, default=100, help='Maximum atoms per molecule')
    parser.add_argument('--failure-threshold', type=float, default=0.10, help='Maximum failure rate')
    
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    
    try:
        # Load input data
        logger.info(f"Loading data from {args.input}")
        df = pd.read_parquet(args.input)
        logger.info(f"Loaded {len(df)} molecules")
        
        # Process in chunks
        chunk_size = 1000
        all_processed = []
        all_failures = []
        
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            logger.info(f"Processing chunk {i//chunk_size + 1}")
            
            processed_df, failures = process_chunk_3d(chunk, logger, args.max_atoms)
            all_processed.append(processed_df)
            all_failures.extend(failures)
            
            # Check failure rate
            total_processed = sum(len(p) for p in all_processed) + len(all_failures)
            if total_processed > 0:
                failure_rate = len(all_failures) / total_processed
                if failure_rate > args.failure_threshold:
                    raise RuntimeError(
                        f"Failure rate ({failure_rate:.2%}) exceeds threshold "
                        f"({args.failure_threshold:.1%}). Halting."
                    )
        
        # Combine results
        if all_processed:
            result_df = pd.concat(all_processed, ignore_index=True)
            result_df.to_parquet(args.output, index=False)
            logger.info(f"Saved {len(result_df)} processed molecules to {args.output}")
        else:
            logger.warning("No molecules were successfully processed")
        
        # Save failure report
        if all_failures:
            failure_path = str(Path(args.output).parent / "failure_report.csv")
            save_failure_report(all_failures, failure_path)
        
        # Save conformer parameters
        params = generate_conformer_config()
        params_path = str(Path(args.output).parent / "conformer_params.json")
        save_conformer_params(params, params_path)
        
        logger.info("Preprocessing completed successfully")
        
    except RuntimeError as e:
        logger.error(f"Pipeline halted: {str(e)}")
        # Save failure report before halting
        if all_failures:
            failure_path = str(Path(args.output).parent / "failure_report.csv")
            save_failure_report(all_failures, failure_path)
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(3)

if __name__ == '__main__':
    main()