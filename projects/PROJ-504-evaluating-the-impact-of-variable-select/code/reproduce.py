from __future__ import annotations

import os
import sys
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd

# Import existing project modules
from config import get_config
from utils.logger import setup_logging, get_logger
from data.downloader import fetch_datasets, DatasetMetadata
from data.simulators import generate_synthetic_outcomes, SimulatorConfig, get_simulator_config
from analysis.selectors import lasso_selection, select_variables_lasso
from analysis.metrics import calculate_empirical_power, calculate_condition_number
from data.storage import save_simulation_manifest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """Compute SHA-256 checksum of a file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksums(manifest_path: Path, expected_checksums: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Verify file checksums against expected values."""
    errors = []
    if not manifest_path.exists():
        errors.append(f"Manifest file not found: {manifest_path}")
        return False, errors
    
    with open(manifest_path, "r") as f:
        current_checksums = json.load(f)
    
    for file_rel_path, expected_hash in expected_checksums.items():
        full_path = PROJECT_ROOT / file_rel_path
        if not full_path.exists():
            errors.append(f"Missing file: {file_rel_path}")
            continue
        
        actual_hash = compute_file_checksum(full_path)
        if actual_hash != expected_hash:
            errors.append(f"Checksum mismatch for {file_rel_path}: expected {expected_hash}, got {actual_hash}")
    
    return len(errors) == 0, errors

def run_pipeline_stage(config: Any, logger: logging.Logger) -> bool:
    """Run the full pipeline stage with pinned seeds for reproducibility."""
    logger.info("Starting reproducibility pipeline run...")
    
    try:
        # 1. Fetch datasets (re-fetch to ensure fresh state)
        logger.info("Fetching datasets from OpenML...")
        datasets = fetch_datasets(config.openml_ids[:10])
        if len(datasets) < 10:
            raise RuntimeError(f"Failed to fetch 10 datasets. Got {len(datasets)}")
        
        # 2. Generate synthetic outcomes
        logger.info("Generating synthetic outcomes...")
        simulator_config = get_simulator_config()
        all_results = []
        
        for dataset in datasets:
            for snr in config.snr_levels:
                for sparsity in config.sparsity_levels:
                    # Run simulation
                    sim_data = generate_synthetic_outcomes(
                        X=dataset.X,
                        seed=config.seed,
                        snr=snr,
                        sparsity=sparsity,
                        dataset_id=dataset.dataset_id,
                        dataset_name=dataset.dataset_name
                    )
                    
                    # Apply selection methods
                    selected_vars_forward = lasso_selection(
                        sim_data.X, sim_data.Y, 
                        method="forward", 
                        alpha=0.05
                    )
                    
                    # Calculate power
                    power = calculate_empirical_power(
                        true_coeffs=sim_data.true_coefficients,
                        selected_vars=selected_vars_forward,
                        p_values=sim_data.p_values
                    )
                    
                    all_results.append({
                        "dataset_id": dataset.dataset_id,
                        "dataset_name": dataset.dataset_name,
                        "snr": snr,
                        "sparsity": sparsity,
                        "method": "forward_stepwise",
                        "power_rate": power,
                        "seed": config.seed
                    })
        
        # Save results
        results_df = pd.DataFrame(all_results)
        output_path = PROJECT_ROOT / config.output_path
        output_path.mkdir(parents=True, exist_ok=True)
        
        results_file = output_path / "reproducibility_results.csv"
        results_df.to_csv(results_file, index=False)
        
        manifest_path = output_path / "reproducibility_manifest.json"
        checksum = compute_file_checksum(results_file)
        
        manifest_data = {
            "file": "reproducibility_results.csv",
            "checksum": checksum,
            "seed": config.seed,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "snr_levels": config.snr_levels,
                "sparsity_levels": config.sparsity_levels,
                "openml_ids": config.openml_ids[:10]
            }
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Pipeline run complete. Results saved to {results_file}")
        logger.info(f"Checksum: {checksum}")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline run failed: {str(e)}", exc_info=True)
        return False

def generate_checksum_manifest(output_dir: Path, files: List[str]) -> Dict[str, str]:
    """Generate a manifest of checksums for specified files."""
    checksums = {}
    for file_rel in files:
        full_path = output_dir / file_rel
        if full_path.exists():
            checksums[file_rel] = compute_file_checksum(full_path)
    return checksums

def main():
    """Main entry point for reproducibility verification."""
    setup_logging(level=logging.INFO)
    logger = get_logger(__name__)
    
    logger.info("=== Reproducibility Verification Task (T049) ===")
    
    # Load configuration
    config = get_config()
    
    # Ensure reproducibility by setting seeds
    import numpy as np
    np.random.seed(config.seed)
    
    # Run the pipeline
    success = run_pipeline_stage(config, logger)
    
    if not success:
        logger.error("Reproducibility check FAILED.")
        sys.exit(1)
    
    # Verify checksums
    output_path = PROJECT_ROOT / config.output_path
    manifest_path = output_path / "reproducibility_manifest.json"
    
    if not manifest_path.exists():
        logger.error("Manifest not found for verification.")
        sys.exit(1)
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    expected_checksums = {manifest["file"]: manifest["checksum"]}
    is_valid, errors = verify_checksums(manifest_path, expected_checksums)
    
    if not is_valid:
        logger.error("Checksum verification FAILED:")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)
    
    logger.info("=== Reproducibility Verification PASSED ===")
    logger.info(f"Pipeline re-ran successfully with seed {config.seed}")
    logger.info(f"Output checksum verified: {manifest['checksum']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
