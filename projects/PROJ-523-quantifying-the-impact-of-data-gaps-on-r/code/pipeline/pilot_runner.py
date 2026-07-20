"""
Pilot runner to execute a fixed minimal subset for runtime estimation.

This script:
1. Runs a minimal simulation (1 realization, 1 algorithm, 1 gap fraction).
2. Records execution time in data/results/pilot_log.json.
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Ensure code directory is in path
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA_RESULTS_DIR, DATA_DERIVED_DIR, DATA_METADATA_DIR
from simulation.generate_maps import generate_cmb_map, save_map_to_fits_wrapper, save_metadata_wrapper
from simulation.utils import generate_random_mask, save_mask_to_fits_wrapper
from gap_filling.harmonic_interp import apply_harmonic_filling
from analysis.power_spectra import compute_power_spectrum
from analysis.metadata_recorder import record_algorithm_metadata

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PILOT_LOG_PATH = Path(DATA_RESULTS_DIR) / "pilot_log.json"

def ensure_directories():
    """Ensure all necessary directories exist."""
    for dir_path in [DATA_RESULTS_DIR, DATA_DERIVED_DIR, DATA_METADATA_DIR]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def run_pilot():
    """
    Execute a pilot run: 1 realization, 1 algorithm, 1 gap fraction.
    Returns metrics including total time and success status.
    """
    ensure_directories()
    
    logger.info("Starting pilot run...")
    start_time = time.time()
    
    pilot_id = "pilot_001"
    realization_id = f"{pilot_id}_realization_0"
    nside = 512
    seed = 42
    gap_fraction = 0.1  # 10%
    algo_name = "harmonic_interp"
    
    try:
        # 1. Generate CMB Map
        logger.info("Generating CMB map...")
        cmb_map, metadata = generate_cmb_map(realization_id, seed=seed, nside=nside)
        
        # 2. Generate Mask (1 gap fraction, random)
        logger.info("Generating mask...")
        mask = generate_random_mask(nside, gap_fraction)
        
        # 3. Save Map and Mask
        logger.info("Saving map and mask...")
        save_map_to_fits_wrapper(cmb_map, realization_id)
        save_mask_to_fits_wrapper(mask, realization_id, gap_fraction)
        
        # 4. Apply Gap Filling (1 algorithm: Harmonic Interp)
        logger.info("Applying gap filling...")
        algo_start = time.time()
        filled_map = apply_harmonic_filling(cmb_map, mask)
        algo_end = time.time()
        algo_duration = algo_end - algo_start
        
        # 5. Compute Power Spectrum
        logger.info("Computing power spectrum...")
        cl = compute_power_spectrum(filled_map, nside)
        
        # 6. Record Algorithm Metadata (T023 requirement)
        logger.info("Recording algorithm metadata...")
        record_algorithm_metadata(
            realization_id=realization_id,
            algo_name=algo_name,
            exec_time_sec=algo_duration
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        metrics = {
            "pilot_id": pilot_id,
            "realization_id": realization_id,
            "status": "success",
            "total_time": duration,
            "algo_duration": algo_duration,
            "realizations_run": 1,
            "algorithms_run": 1,
            "gap_fractions_run": 1,
            "nside": nside,
            "gap_fraction": gap_fraction,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save metrics to pilot_log.json (T007 requirement)
        with open(PILOT_LOG_PATH, "w") as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Pilot run completed successfully in {duration:.2f} seconds.")
        logger.info(f"Metrics saved to {PILOT_LOG_PATH}")
        
        return metrics
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"Pilot run failed: {e}", exc_info=True)
        
        metrics = {
            "pilot_id": pilot_id,
            "status": "failed",
            "error": str(e),
            "total_time": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(PILOT_LOG_PATH, "w") as f:
            json.dump(metrics, f, indent=2)
        
        return metrics

def main():
    """Entry point for pilot_runner."""
    metrics = run_pilot()
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()