import csv
import json
import logging
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from utils.error_utils import ConvergenceError, handle_convergence_failure
from utils.logging_utils import setup_logger
from dftb_calculator import calculate_descriptors_for_molecule
from physical_validator import validate_homo_lumo_relationship

# Constants
LOG_FILE = "logs/dft_execution.log"
STRUCTURAL_FAILURES_LOG = "logs/structural_failures.log"
CONVERGENCE_FAILURES_LOG = "logs/convergence_failures.log"
OOM_FAILURES_LOG = "logs/oom_failures.log"

def setup_pipeline_logging():
    """Set up logging for the descriptor pipeline."""
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = setup_logger("descriptor_pipeline", LOG_FILE)
    logger.setLevel(logging.INFO)
    return logger

def write_geometry_xyz(molecule_id, coordinates, output_dir):
    """
    Write optimized geometry to XYZ file.
    
    Args:
        molecule_id: Unique identifier for the molecule
        coordinates: List of tuples (element, x, y, z)
        output_dir: Directory to write the file
    """
    output_path = Path(output_dir) / f"{molecule_id}.xyz"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(f"{len(coordinates)}\n")
        f.write(f"{molecule_id}\n")
        for element, x, y, z in coordinates:
            f.write(f"{element} {x:.6f} {y:.6f} {z:.6f}\n")

def log_execution_status(logger, molecule_id, command, exit_code, duration, peak_memory_mb):
    """
    Log execution status as a JSON line to dft_execution.log.
    
    Args:
        logger: Logger instance
        molecule_id: Unique identifier for the molecule
        command: Command executed
        exit_code: Exit code of the command
        duration: Execution duration in seconds
        peak_memory_mb: Peak memory usage in MB
    """
    log_entry = {
        "molecule_id": molecule_id,
        "command": command,
        "exit_code": exit_code,
        "duration": duration,
        "peak_memory_mb": peak_memory_mb
    }
    
    # Write JSON line to log file
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def run_pipeline(input_df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """
    Run the descriptor pipeline on the input dataset.
    
    Args:
        input_df: DataFrame containing SMILES and molecule_id
        output_dir: Directory to save optimized geometries and descriptors
        
    Returns:
        DataFrame with computed descriptors
    """
    logger = setup_pipeline_logging()
    logger.info("Starting descriptor pipeline")
    
    results = []
    failed_molecules = []
    
    for idx, row in input_df.iterrows():
        molecule_id = row['molecule_id']
        smiles = row['SMILES']
        
        logger.info(f"Processing molecule: {molecule_id}")
        
        start_time = time.time()
        try:
            # Calculate descriptors
            command = f"dftb+ {molecule_id}"
            descriptors, coordinates, exit_code, peak_memory_mb = calculate_descriptors_for_molecule(
                molecule_id, smiles
            )
            
            duration = time.time() - start_time
            
            # Log execution status
            log_execution_status(
                logger, molecule_id, command, exit_code, duration, peak_memory_mb
            )
            
            # Validate HOMO < LUMO
            if not validate_homo_lumo_relationship(descriptors['HOMO_energy'], descriptors['LUMO_energy']):
                log_path = Path(STRUCTURAL_FAILURES_LOG)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, 'a') as f:
                    f.write(f"{molecule_id},{datetime.now().isoformat()},structural_failure,HOMO >= LUMO\n")
                logger.warning(f"Structural validation failed for {molecule_id}: HOMO >= LUMO")
                continue
            
            # Write optimized geometry
            write_geometry_xyz(molecule_id, coordinates, output_dir)
            
            # Add to results
            results.append({
                'molecule_id': molecule_id,
                'HOMO_energy': descriptors['HOMO_energy'],
                'LUMO_energy': descriptors['LUMO_energy'],
                'mayer_bond_order': descriptors['mayer_bond_order']
            })
            
        except ConvergenceError as e:
            duration = time.time() - start_time
            log_execution_status(
                logger, molecule_id, f"dftb+ {molecule_id}", -1, duration, 0
            )
            handle_convergence_failure(molecule_id, str(e), CONVERGENCE_FAILURES_LOG)
            logger.error(f"Convergence failed for {molecule_id}: {e}")
            failed_molecules.append(molecule_id)
            
        except Exception as e:
            duration = time.time() - start_time
            log_execution_status(
                logger, molecule_id, f"dftb+ {molecule_id}", -1, duration, 0
            )
            logger.error(f"Unexpected error for {molecule_id}: {e}")
            failed_molecules.append(molecule_id)
    
    logger.info(f"Pipeline completed. Success: {len(results)}, Failed: {len(failed_molecules)}")
    
    return pd.DataFrame(results)

def main():
    """Main entry point for the descriptor pipeline."""
    parser = argparse.ArgumentParser(description="Run descriptor pipeline on barrier dataset")
    parser.add_argument("--input", type=str, default="data/raw/barrier_dataset.csv",
                      help="Path to input CSV file")
    parser.add_argument("--output", type=str, default="data/descriptors_semi.csv",
                      help="Path to output CSV file")
    parser.add_argument("--geometry-dir", type=str, default="data/optimized_geometries",
                      help="Directory to save optimized geometries")
    
    args = parser.parse_args()
    
    # Load input data
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    input_df = pd.read_csv(args.input)
    
    # Run pipeline
    output_df = run_pipeline(input_df, args.geometry_dir)
    
    # Write output
    output_df.to_csv(args.output, index=False)
    print(f"Descriptors written to {args.output}")

if __name__ == "__main__":
    main()