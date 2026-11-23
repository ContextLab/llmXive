"""
Orchestrate Green-Kubo batch execution for all N=10 samples.

This script iterates through all valid XYZ samples in data/raw/,
runs the Green-Kubo simulation for each using the existing green_kubo.py
module, and saves the resulting ThermalSample objects.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config, get_paths
from simulation.green_kubo import run_green_kubo_for_sample
from simulation.thermal_sample_saver import save_thermal_sample, create_thermal_sample
from ingestion.sample_validator import is_valid_xyz_file, scan_raw_directory
from ingestion.graph_builder import build_graph_from_xyz
from metrics.topology_extractor import extract_topology_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    config = get_config()
    paths = get_paths()

    raw_dir = paths["data_raw"]
    processed_conductivity_dir = paths["data_processed_conductivities"]

    # Ensure output directory exists
    os.makedirs(processed_conductivity_dir, exist_ok=True)

    # 1. Scan for valid XYZ files
    logger.info(f"Scanning {raw_dir} for valid XYZ files...")
    xyz_files = scan_raw_directory(raw_dir)

    if not xyz_files:
        logger.error("No valid XYZ files found in data/raw/. Aborting.")
        sys.exit(1)

    logger.info(f"Found {len(xyz_files)} valid XYZ files.")

    # 2. Process each sample
    results = []
    failed_samples = []

    for xyz_path in xyz_files:
        sample_id = xyz_path.stem
        logger.info(f"Processing sample: {sample_id}")

        try:
            # A. Build Graph (if not already done, but we assume T012/T015a ran)
            # For this orchestrator, we rely on the graph builder to handle the XYZ
            # However, the green_kubo runner typically needs the atomic structure.
            # We pass the path directly to the runner which handles the LAMMPS setup.

            # B. Run Green-Kubo Simulation
            # This function returns a dict compatible with ThermalSample schema
            logger.info(f"Running Green-Kubo for {sample_id}...")
            result = run_green_kubo_for_sample(
                xyz_path=str(xyz_path),
                sample_id=sample_id,
                config=config
            )

            if result is None:
                logger.warning(f"Green-Kubo returned None for {sample_id}. Skipping.")
                failed_samples.append(sample_id)
                continue

            # C. Validate Result
            required_keys = ["graph_id", "conductivity", "converged", "metadata"]
            if not all(k in result for k in required_keys):
                logger.error(f"Result for {sample_id} missing required keys. Skipping.")
                failed_samples.append(sample_id)
                continue

            # D. Save ThermalSample
            # The save function expects a dict or object matching the schema
            saved_path = save_thermal_sample(
                thermal_data=result,
                output_dir=processed_conductivity_dir
            )

            if saved_path:
                logger.info(f"Saved thermal sample to {saved_path}")
                results.append({
                    "sample_id": sample_id,
                    "status": "success",
                    "output_file": str(saved_path),
                    "conductivity": result.get("conductivity"),
                    "converged": result.get("converged")
                })
            else:
                logger.error(f"Failed to save thermal sample for {sample_id}.")
                failed_samples.append(sample_id)

        except Exception as e:
            logger.error(f"Error processing {sample_id}: {e}", exc_info=True)
            failed_samples.append(sample_id)

    # 3. Summary
    logger.info(f"Batch execution complete. Success: {len(results)}, Failed: {len(failed_samples)}")
    
    # Write summary report
    summary_path = processed_conductivity_dir / "batch_execution_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            "total_samples": len(xyz_files),
            "successful": len(results),
            "failed": len(failed_samples),
            "failed_ids": failed_samples,
            "results": results
        }, f, indent=2)
    
    logger.info(f"Summary written to {summary_path}")

    if failed_samples:
        logger.warning(f"Failed to process {len(failed_samples)} samples.")
        # Do not exit with error code if some succeeded, but log clearly
    else:
        logger.info("All samples processed successfully.")

if __name__ == "__main__":
    main()
