import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Import local utilities
from utils.logging import get_logger
from utils.conformer_config import generate_conformer_config
from utils.config import get_project_root, get_data_dir

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

def generate_3d_conformer(mol: Chem.Mol, params: Dict[str, Any]) -> Optional[Chem.Mol]:
    """
    Generate a 3D conformer for a molecule using ETKDG.
    
    Args:
        mol: RDKit Mol object (2D)
        params: Dictionary of conformer generation parameters
      
    Returns:
        RDKit Mol object with 3D coordinates, or None if generation fails
    """
    try:
        # Ensure the molecule has hydrogens added for conformer generation
        mol_h = Chem.AddHs(mol)
        
        # Generate conformer
        # Use the parameters from the config
        embed_params = {
            'maxAttempts': params.get('maxAttempts', 500),
            'useRandomCoords': params.get('useRandomCoords', False),
            'pruneRmsThresh': params.get('pruneRmsThresh', -1.0),
        }
        
        # Attempt ETKDG embedding
        embed_id = AllChem.EmbedMolecule(mol_h, AllChem.ETKDGv3(), **embed_params)
        
        if embed_id == -1:
            # Fallback to random coords if ETKDG fails
            embed_id = AllChem.EmbedMolecule(mol_h, AllChem.RandomCoords(), **embed_params)
            if embed_id == -1:
                return None
        
        # Optimize geometry
        mmff_props = AllChem.MMFFGetMoleculeProperties(mol_h)
        if mmff_props is None:
            # If MMFF fails, try UFF
            AllChem.UFFOptimizeMolecule(mol_h, maxIters=params.get('maxIters', 200))
        else:
            ff = AllChem.MMFFGetMoleculeForceField(mol_h, mmff_props)
            if ff is not None:
                ff.Minimize(maxIts=params.get('maxIters', 200))
            else:
                AllChem.UFFOptimizeMolecule(mol_h, maxIters=params.get('maxIters', 200))
        
        # Remove hydrogens to match original structure
        mol_3d = Chem.RemoveHs(mol_h)
        return mol_3d
        
    except Exception as e:
        logger.debug(f"Conformer generation failed: {str(e)}")
        return None

def calculate_sasa(mol: Chem.Mol) -> Optional[float]:
    """
    Calculate Solvent Accessible Surface Area (SASA) for a molecule.
    
    Args:
        mol: RDKit Mol object with 3D coordinates
        
    Returns:
        SASA value in Angstroms^2, or None if calculation fails
    """
    try:
        # Ensure molecule has 3D coordinates
        if not mol.GetNumConformers() > 0:
            return None
        if mol.GetConformer().Is3D() == False:
            return None
        
        # Calculate SASA using RDKit's built-in function
        # Default probe radius is 1.4 Angstroms (water)
        sasa = rdMolDescriptors.CalcSASA(mol)
        return float(sasa)
        
    except Exception as e:
        logger.debug(f"SASA calculation failed: {str(e)}")
        return None

def process_molecule_with_3d(smiles: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single molecule: generate 3D conformer and calculate SASA.
    
    Args:
        smiles: SMILES string
        params: Conformer generation parameters
        
    Returns:
        Dictionary with 'smiles', 'sasa', 'success' keys, or None if critical failure
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {'smiles': smiles, 'success': False, 'error': 'Invalid SMILES'}
        
        # Generate 3D conformer
        mol_3d = generate_3d_conformer(mol, params)
        
        if mol_3d is None:
            return {'smiles': smiles, 'success': False, 'error': 'Conformer generation failed'}
        
        # Calculate SASA
        sasa = calculate_sasa(mol_3d)
        
        if sasa is None:
            return {'smiles': smiles, 'success': False, 'error': 'SASA calculation failed'}
        
        return {
            'smiles': smiles,
            'sasa': sasa,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        return {'smiles': smiles, 'success': False, 'error': str(e)}

def process_chunk_with_3d(chunk: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Process a chunk of molecules with 3D conformer generation and SASA calculation.
    
    Args:
        chunk: DataFrame with at least 'smiles' column
        params: Conformer generation parameters
        
    Returns:
        Tuple of (processed_chunk, failure_records)
    """
    results = []
    failures = []
    success_count = 0
    total_count = len(chunk)
    
    for idx, row in chunk.iterrows():
        result = process_molecule_with_3d(row['smiles'], params)
        results.append(result)
        
        if result['success']:
            success_count += 1
        else:
            failures.append({
                'smiles': result['smiles'],
                'error': result['error'],
                'index': idx
            })
    
    # Create result DataFrame
    result_df = pd.DataFrame(results)
    result_df = result_df.merge(chunk, on='smiles', how='left')
    
    # Log progress
    success_rate = success_count / total_count if total_count > 0 else 0
    logger.info(f"Processed {total_count} molecules: {success_count} success ({success_rate:.2%})")
    
    return result_df, failures

def main():
    """
    Main entry point for T015: 3D conformer generation and SASA calculation.
    
    This task:
    1. Loads processed data from T014b (graphs_with_mw.parquet)
    2. Invokes T008b utility to generate and save conformer_config.json
    3. Processes molecules in chunks to generate 3D conformers and SASA
    4. Halts with critical error if >10% failure rate
    5. Generates failure_report.csv if failure rate exceeds threshold
    """
    # Setup logging
    logger = get_logger(__name__)
    logger.info("Starting T015: 3D conformer generation and SASA calculation")
    
    # Get project paths
    project_root = get_project_root()
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    
    # Input file from T014b
    input_file = processed_dir / "graphs_with_mw.parquet"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Load data
    logger.info(f"Loading data from {input_file}")
    df = pd.read_parquet(input_file)
    logger.info(f"Loaded {len(df)} molecules")
    
    # Validate required columns
    required_cols = ['smiles', 'node_features', 'edge_features', 'molecular_weight']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Generate and save conformer config (T008b utility)
    logger.info("Generating conformer configuration (T008b utility)")
    config = generate_conformer_config()
    config_path = processed_dir / "conformer_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Conformer config saved to {config_path}")
    
    # Process in chunks
    chunk_size = 100  # Process 100 molecules at a time
    all_results = []
    all_failures = []
    total_processed = 0
    
    logger.info(f"Processing molecules in chunks of {chunk_size}")
    
    for start_idx in range(0, len(df), chunk_size):
        end_idx = min(start_idx + chunk_size, len(df))
        chunk = df.iloc[start_idx:end_idx]
        
        chunk_results, chunk_failures = process_chunk_with_3d(chunk, config)
        all_results.append(chunk_results)
        all_failures.extend(chunk_failures)
        
        total_processed += len(chunk)
        logger.info(f"Progress: {total_processed}/{len(df)} molecules processed")
    
    # Combine results
    final_df = pd.concat(all_results, ignore_index=True)
    
    # Calculate failure rate
    total_molecules = len(df)
    failed_molecules = len(all_failures)
    failure_rate = failed_molecules / total_molecules if total_molecules > 0 else 0
    
    logger.info(f"Total molecules: {total_molecules}")
    logger.info(f"Failed molecules: {failed_molecules}")
    logger.info(f"Failure rate: {failure_rate:.2%}")
    
    # Check failure rate threshold
    if failure_rate > 0.10:
        logger.critical(f"Failure rate ({failure_rate:.2%}) exceeds 10% threshold!")
        
        # Generate failure report BEFORE halting
        failure_report_path = processed_dir / "failure_report.csv"
        failure_df = pd.DataFrame(all_failures)
        if len(failure_df) > 0:
            # Add some analysis of failed molecules
            if 'molecular_weight' in final_df.columns:
                failure_df = failure_df.merge(
                    final_df[['smiles', 'molecular_weight']], 
                    on='smiles', 
                    how='left'
                )
            
            failure_df.to_csv(failure_report_path, index=False)
            logger.info(f"Failure report saved to {failure_report_path}")
            
            # Log summary of failures
            error_counts = failure_df['error'].value_counts()
            logger.info("Failure breakdown:")
            for error, count in error_counts.items():
                logger.info(f"  {error}: {count}")
        
        raise RuntimeError(f"Conformer generation failure rate ({failure_rate:.2%}) exceeds 10% threshold. Halting pipeline.")
    
    # Save successful results
    output_file = processed_dir / "graphs_with_sasa.parquet"
    # Keep only successful entries
    successful_df = final_df[final_df['success'] == True].copy()
    
    # Ensure SASA column is float
    if 'sasa' in successful_df.columns:
        successful_df['sasa'] = successful_df['sasa'].astype(float)
    
    successful_df.to_parquet(output_file, index=False)
    logger.info(f"Successfully saved {len(successful_df)} molecules to {output_file}")
    
    # Log final statistics
    logger.info("T015 completed successfully")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Total processed: {total_molecules}")
    logger.info(f"Successful: {len(successful_df)}")
    logger.info(f"Failed: {failed_molecules}")
    logger.info(f"Success rate: {len(successful_df)/total_molecules:.2%}")
    
    return {
        'output_file': str(output_file),
        'total_processed': total_molecules,
        'successful': len(successful_df),
        'failed': failed_molecules,
        'failure_rate': failure_rate
    }

if __name__ == "__main__":
    main()