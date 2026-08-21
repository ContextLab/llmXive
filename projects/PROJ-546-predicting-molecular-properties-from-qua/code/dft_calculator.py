"""
DFT Calculator for Molecular Property Prediction
Implements T020b: DFT calculation logic using Psi4 for B3LYP/def2-SVP
"""

import argparse
import csv
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold

# Import utilities from existing modules
from utils.logging_utils import setup_logger, log_psi4_invocation
from utils.error_utils import ConvergenceError, handle_convergence_failure

# Constants
RANDOM_STATE = 42
PSI4_EXECUTABLE = "psi4"
OUTPUT_FILE = "data/descriptors_dft.csv"
LOCKED_SPLITS_FILE = "data/locked_splits.json"
LOG_FILE = "logs/dft_execution.log"
CONVERGENCE_LOG = "logs/convergence_failures.log"
GEOMETRY_DIR = "data/optimized_geometries"

def log_setup():
    """Setup logging for DFT calculations."""
    logger = setup_logger("dft_calculator", LOG_FILE)
    return logger

def load_subset_indices(subset_file: str = "data/subset_indices.csv") -> List[int]:
    """Load the selected subset indices from T020a."""
    if not os.path.exists(subset_file):
        raise FileNotFoundError(f"Subset file not found: {subset_file}")
    
    df = pd.read_csv(subset_file)
    return df['molecule_id'].tolist()

def get_geometry_path(molecule_id: str) -> Path:
    """Get the path to the optimized geometry file for a molecule."""
    return Path(GEOMETRY_DIR) / f"{molecule_id}.xyz"

def parse_xyz_to_psi4_input(xyz_path: Path) -> str:
    """
    Parse XYZ file and convert to Psi4 input format.
    Returns a string ready for Psi4 input.
    """
    if not xyz_path.exists():
        raise FileNotFoundError(f"Geometry file not found: {xyz_path}")
    
    with open(xyz_path, 'r') as f:
        lines = f.readlines()
    
    # Skip header (atom count) and comment line
    atoms = []
    for line in lines[2:]:
        parts = line.strip().split()
        if len(parts) >= 4:
            element = parts[0]
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            atoms.append((element, x, y, z))
    
    # Build Psi4 input
    psi4_input = "memory 2 GB\n"
    psi4_input += "b3lyp/def2-svp\n"
    psi4_input += "geometry {\n"
    for element, x, y, z in atoms:
        psi4_input += f"  {element}  {x:.6f}  {y:.6f}  {z:.6f}\n"
    psi4_input += "}\n"
    psi4_input += "energy('optimize')\n"
    
    return psi4_input

def run_psi4_calculation(molecule_id: str, psi4_input: str, temp_dir: Path) -> Tuple[bool, str, float]:
    """
    Run Psi4 calculation for a single molecule.
    Returns: (success, output_text, duration_seconds)
    """
    input_file = temp_dir / "input.dat"
    output_file = temp_dir / "output.log"
    
    with open(input_file, 'w') as f:
        f.write(psi4_input)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [PSI4_EXECUTABLE, str(input_file), str(output_file)],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per molecule
            cwd=temp_dir
        )
        
        duration = time.time() - start_time
        
        if result.returncode != 0:
            logging.warning(f"Psi4 failed for {molecule_id}: {result.stderr}")
            return False, result.stderr, duration
        
        with open(output_file, 'r') as f:
            output_text = f.read()
        
        return True, output_text, duration
        
    except subprocess.TimeoutExpired:
        logging.error(f"Psi4 timeout for {molecule_id}")
        return False, "Timeout", time.time() - start_time
    except Exception as e:
        logging.error(f"Psi4 error for {molecule_id}: {str(e)}")
        return False, str(e), time.time() - start_time

def parse_psi4_output(output_text: str) -> Optional[Dict[str, float]]:
    """
    Parse Psi4 output to extract HOMO and LUMO energies.
    Returns dict with HOMO_energy and LUMO_energy in eV, or None if parsing fails.
    """
    try:
        # Look for HOMO/LUMO in output
        homo_match = re.search(r'HOMO.*?(-?\d+\.\d+)', output_text, re.IGNORECASE)
        lumo_match = re.search(r'LUMO.*?(-?\d+\.\d+)', output_text, re.IGNORECASE)
        
        if not homo_match or not lumo_match:
            return None
        
        homo_energy = float(homo_match.group(1))
        lumo_energy = float(lumo_match.group(1))
        
        # Convert to eV if necessary (Psi4 typically outputs in Hartree)
        # Assuming Hartree to eV conversion (1 Hartree = 27.2114 eV)
        hartree_to_ev = 27.2114
        homo_ev = homo_energy * hartree_to_ev
        lumo_ev = lumo_energy * hartree_to_ev
        
        return {
            'HOMO_energy': homo_ev,
            'LUMO_energy': lumo_ev
        }
        
    except Exception as e:
        logging.warning(f"Failed to parse Psi4 output: {str(e)}")
        return None

def generate_locked_splits(target: np.ndarray, n_splits: int = 5) -> Dict[str, List[List[int]]]:
    """
    Generate locked stratified splits using StratifiedKFold.
    Ensures the same split indices are used for both Semi-Empirical and DFT models.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    splits = []
    
    for train_idx, test_idx in skf.split(np.zeros(len(target)), target):
        splits.append({
            'train': train_idx.tolist(),
            'test': test_idx.tolist()
        })
    
    return {
        'random_state': RANDOM_STATE,
        'n_splits': n_splits,
        'splits': splits
    }

def write_locked_splits(splits_data: Dict, output_path: str = LOCKED_SPLITS_FILE):
    """Write locked splits to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(splits_data, f, indent=2)
    logging.info(f"Locked splits written to {output_path}")

def run_dft_calculation_on_subset(
    subset_indices: List[str],
    descriptors_output: str = OUTPUT_FILE,
    locked_splits_output: str = LOCKED_SPLITS_FILE
) -> pd.DataFrame:
    """
    Run DFT calculations on the selected subset.
    Imports geometries from T013c output, handles missing files, and writes results.
    """
    logger = logging.getLogger("dft_calculator")
    results = []
    failed_molecules = []
    
    # Read the full dataset to get target values for splitting
    full_data_path = "data/raw/barrier_dataset.csv"
    if not os.path.exists(full_data_path):
        raise FileNotFoundError(f"Full dataset not found: {full_data_path}")
    
    full_df = pd.read_csv(full_data_path)
    
    # Filter to subset
    subset_df = full_df[full_df['molecule_id'].isin(subset_indices)].copy()
    
    if len(subset_df) == 0:
        logger.error("No valid molecules in subset after filtering")
        return pd.DataFrame()
    
    # Create temp directory for Psi4 runs
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for idx, row in subset_df.iterrows():
            molecule_id = row['molecule_id']
            geometry_path = get_geometry_path(molecule_id)
            
            # Check for missing geometry
            if not geometry_path.exists():
                logger.warning(f"Missing geometry for {molecule_id}, excluding from DFT subset")
                failed_molecules.append({
                    'molecule_id': molecule_id,
                    'status': 'missing_geometry',
                    'error': 'Geometry file not found'
                })
                continue
            
            try:
                # Parse XYZ to Psi4 input
                psi4_input = parse_xyz_to_psi4_input(geometry_path)
                
                # Run Psi4
                success, output_text, duration = run_psi4_calculation(
                    molecule_id, psi4_input, temp_path
                )
                
                if not success:
                    logger.warning(f"Psi4 failed for {molecule_id}")
                    failed_molecules.append({
                        'molecule_id': molecule_id,
                        'status': 'psi4_failure',
                        'error': output_text[:200]
                    })
                    continue
                
                # Parse output
                energies = parse_psi4_output(output_text)
                
                if energies is None:
                    logger.warning(f"Failed to parse Psi4 output for {molecule_id}")
                    failed_molecules.append({
                        'molecule_id': molecule_id,
                        'status': 'parse_failure',
                        'error': 'Could not extract HOMO/LUMO'
                    })
                    continue
                
                # Validate HOMO < LUMO
                if energies['HOMO_energy'] >= energies['LUMO_energy']:
                    logger.warning(f"Invalid HOMO/LUMO relationship for {molecule_id}")
                    failed_molecules.append({
                        'molecule_id': molecule_id,
                        'status': 'physical_violation',
                        'error': f"HOMO ({energies['HOMO_energy']}) >= LUMO ({energies['LUMO_energy']})"
                    })
                    continue
                
                # Log successful calculation
                log_psi4_invocation(molecule_id, duration, success)
                
                # Add to results
                results.append({
                    'molecule_id': molecule_id,
                    'HOMO_energy': energies['HOMO_energy'],
                    'LUMO_energy': energies['LUMO_energy'],
                    'mayer_bond_order': 0.0  # Placeholder, to be calculated if needed
                })
                
            except Exception as e:
                logger.error(f"Error processing {molecule_id}: {str(e)}")
                failed_molecules.append({
                    'molecule_id': molecule_id,
                    'status': 'exception',
                    'error': str(e)
                })
    
    # Log failures
    if failed_molecules:
        with open(CONVERGENCE_LOG, 'a') as f:
            for failure in failed_molecules:
                f.write(json.dumps(failure) + '\n')
    
    # Create output DataFrame
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(descriptors_output, index=False)
        logger.info(f"Wrote {len(result_df)} DFT descriptors to {descriptors_output}")
    else:
        # Create empty file with headers
        pd.DataFrame(columns=['molecule_id', 'HOMO_energy', 'LUMO_energy', 'mayer_bond_order']).to_csv(
            descriptors_output, index=False
        )
        logger.warning("No successful DFT calculations, wrote empty output file")
    
    # Generate locked splits for model training
    if len(result_df) >= 2:
        # Use experimental_barrier from original data for stratification
        subset_target = full_df[full_df['molecule_id'].isin(result_df['molecule_id'].tolist())]['experimental_barrier'].values
        
        if len(subset_target) >= 2:
            # Ensure at least 2 classes for stratification
            if len(np.unique(subset_target)) < 2:
                # Fallback: use binned values
                bins = min(5, len(subset_target))
                subset_target = pd.qcut(subset_target, q=bins, labels=False, duplicates='drop')
            
            splits_data = generate_locked_splits(subset_target)
            write_locked_splits(splits_data, locked_splits_output)
        else:
            logger.warning("Not enough samples for stratified splitting")
    
    return result_df

def main():
    """Main entry point for DFT calculator."""
    parser = argparse.ArgumentParser(description="Run DFT calculations on selected subset")
    parser.add_argument('--subset-file', default='data/subset_indices.csv',
                      help='Path to subset indices CSV')
    parser.add_argument('--output', default=OUTPUT_FILE,
                      help='Output CSV path')
    parser.add_argument('--splits-output', default=LOCKED_SPLITS_FILE,
                      help='Locked splits output path')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = log_setup()
    logger.info("Starting DFT calculations")
    
    try:
        # Load subset
        subset_indices = load_subset_indices(args.subset_file)
        logger.info(f"Loaded {len(subset_indices)} molecules for DFT calculation")
        
        # Run calculations
        result_df = run_dft_calculation_on_subset(
            subset_indices,
            args.output,
            args.splits_output
        )
        
        logger.info(f"DFT calculations complete. {len(result_df)} molecules processed.")
        
    except Exception as e:
        logger.error(f"Fatal error in DFT calculator: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
