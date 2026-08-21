"""
T013c: Descriptor Pipeline Implementation
Orchestrates the full-dataset pipeline for User Story 1.
"""
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Import existing utilities and calculators
from dftb_calculator import calculate_descriptors_for_molecule
from error_handlers import ConvergenceError, OOMError, setup_logger, handle_convergence_failure, handle_oom
from physical_validator import validate_homo_lumo_relationship, log_structural_failure
from utils.logging_utils import log_dftb_invocation, log_resource_snapshot

def setup_pipeline_logging(log_dir: Path) -> logging.Logger:
    """Setup dedicated logger for the pipeline."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline_execution.log"
    
    logger = logging.getLogger("descriptor_pipeline")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def write_geometry_xyz(molecule_id: str, coordinates: List[Dict[str, Any]], output_dir: Path):
    """
    Save optimized geometry to XYZ format.
    Format:
      <atom_count>
      <molecule_id>
      <Element> <x> <y> <z>
      ...
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{molecule_id}.xyz"
    
    with open(filepath, 'w') as f:
        f.write(f"{len(coordinates)}\n")
        f.write(f"{molecule_id}\n")
        for atom in coordinates:
            f.write(f"{atom['element']} {atom['x']} {atom['y']} {atom['z']}\n")

def run_pipeline(input_df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """
    Orchestrate the full-dataset pipeline.
    
    Args:
        input_df: DataFrame containing SMILES and molecule_id
        output_dir: Directory to write outputs (descriptors CSV and geometries)
        
    Returns:
        DataFrame with calculated descriptors
    """
    # Setup paths
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    geometries_dir = output_path.parent / "optimized_geometries"
    logs_dir = output_path.parent / "logs"
    
    # Setup logging
    logger = setup_pipeline_logging(logs_dir)
    logger.info("Starting descriptor pipeline")
    
    # Initialize result storage
    results = []
    structural_failures = []
    skipped_count = 0
    success_count = 0
    
    # Iterate over molecules
    for idx, row in input_df.iterrows():
        molecule_id = row['molecule_id']
        smiles = row['SMILES']
        
        logger.info(f"Processing molecule {molecule_id}")
        start_time = time.time()
        
        try:
            # 1. Calculate descriptors using DFTB+
            # This invokes DFTB+ for geometry optimization and descriptor extraction
            descriptors = calculate_descriptors_for_molecule(molecule_id, smiles, logs_dir)
            
            if descriptors is None:
                logger.warning(f"Skipping {molecule_id}: DFTB+ calculation failed or returned None")
                skipped_count += 1
                continue
            
            # 2. Validate HOMO < LUMO (Physical Constraint)
            homo = descriptors.get('HOMO_energy')
            lumo = descriptors.get('LUMO_energy')
            
            if homo is None or lumo is None:
                logger.warning(f"Skipping {molecule_id}: Missing HOMO or LUMO energy")
                skipped_count += 1
                continue
                
            if not validate_homo_lumo_relationship(homo, lumo):
                error_msg = f"HOMO ({homo}) >= LUMO ({lumo})"
                log_structural_failure(molecule_id, logs_dir, "PHYSICAL_VIOLATION", error_msg)
                logger.warning(f"Skipping {molecule_id}: {error_msg}")
                structural_failures.append({
                    "molecule_id": molecule_id,
                    "timestamp": datetime.now().isoformat(),
                    "error_code": "PHYSICAL_VIOLATION",
                    "error_message": error_msg
                })
                skipped_count += 1
                continue
            
            # 3. Export Geometry
            if 'geometry' in descriptors and descriptors['geometry']:
                write_geometry_xyz(molecule_id, descriptors['geometry'], geometries_dir)
                logger.debug(f"Geometry saved for {molecule_id}")
            
            # 4. Log invocation details
            duration = time.time() - start_time
            log_resource_snapshot(logs_dir, "dftb", molecule_id, duration)
            
            # 5. Store results
            results.append({
                "molecule_id": molecule_id,
                "HOMO_energy": float(homo),
                "LUMO_energy": float(lumo),
                "mayer_bond_order": float(descriptors.get('mayer_bond_order', 0.0))
            })
            success_count += 1
            
        except ConvergenceError as e:
            handle_convergence_failure(molecule_id, str(e), logs_dir)
            logger.error(f"Convergence failure for {molecule_id}: {e}")
            skipped_count += 1
        except OOMError as e:
            handle_oom(molecule_id, str(e), logs_dir)
            logger.error(f"OOM failure for {molecule_id}: {e}")
            skipped_count += 1
        except Exception as e:
            logger.exception(f"Unexpected error for {molecule_id}: {e}")
            skipped_count += 1
    
    # Write final CSV
    output_csv = output_path / "descriptors_semi.csv"
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_csv, index=False)
        logger.info(f"Successfully wrote {len(results)} descriptors to {output_csv}")
    else:
        logger.warning("No successful descriptors to write")
        # Write empty CSV with headers to satisfy schema requirements
        pd.DataFrame(columns=["molecule_id", "HOMO_energy", "LUMO_energy", "mayer_bond_order"]).to_csv(output_csv, index=False)
    
    # Log summary
    logger.info(f"Pipeline complete. Success: {success_count}, Skipped: {skipped_count}, Structural Failures: {len(structural_failures)}")
    
    return df_results if results else pd.DataFrame(columns=["molecule_id", "HOMO_energy", "LUMO_energy", "mayer_bond_order"])

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Run descriptor pipeline on barrier dataset")
    parser.add_argument("--input", type=str, default="data/raw/barrier_dataset.csv",
                      help="Path to input CSV with SMILES")
    parser.add_argument("--output", type=str, default="data",
                      help="Output directory for descriptors and geometries")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Load input data
    try:
        df = pd.read_csv(input_path)
        required_cols = ['molecule_id', 'SMILES']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: Input CSV missing required columns. Found: {df.columns.tolist()}")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading input data: {e}")
        sys.exit(1)
    
    # Run pipeline
    try:
        result_df = run_pipeline(df, args.output)
        print(f"Pipeline completed. Output written to {args.output}/descriptors_semi.csv")
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
