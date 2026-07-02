"""
Pilot Runner for Runtime Estimation.

Executes a fixed minimal subset of the analysis pipeline:
- 1 realization
- 1 algorithm (Harmonic Interpolation)
- 1 gap fraction (10%)

Outputs execution metrics to data/results/pilot_log.json for budget calculation.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import N_SIDE, GAP_FRACTIONS, DATA_DERIVED_DIR, DATA_RESULTS_DIR
from simulation.generate_maps import generate_cmb_map, save_map_to_fits_wrapper, save_metadata_wrapper
from simulation.utils import generate_random_mask, save_mask_to_fits_wrapper
from gap_filling.harmonic_interp import apply_harmonic_filling
from analysis.power_spectra import compute_power_spectrum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "pilot_runner.log")
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required output directories exist."""
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

def run_pilot():
    """
    Execute the pilot run: 1 realization, 1 algorithm, 1 gap fraction.
    """
    logger.info("Starting Pilot Run for runtime estimation...")
    start_time = time.time()

    # Configuration for pilot
    pilot_config = {
        "realization_id": 0,
        "gap_fraction": 0.10,  # 10% gap
        "algorithm": "harmonic_interp",
        "n_side": N_SIDE
    }

    try:
        # Step 1: Generate CMB Map
        logger.info(f"Generating CMB map for realization {pilot_config['realization_id']}...")
        t0 = time.time()
        map_data = generate_cmb_map(pilot_config['realization_id'], seed=42)
        t1 = time.time()
        gen_time = t1 - t0
        logger.info(f"Map generation completed in {gen_time:.2f}s")

        # Step 2: Save Map
        map_path = DATA_DERIVED_DIR / f"cmb_map_r{pilot_config['realization_id']}.fits"
        save_map_to_fits_wrapper(map_data, map_path, pilot_config['realization_id'])
        logger.info(f"Map saved to {map_path}")

        # Step 3: Generate Mask
        logger.info(f"Generating random mask with fraction {pilot_config['gap_fraction']}...")
        t0 = time.time()
        mask_data = generate_random_mask(N_SIDE, pilot_config['gap_fraction'], seed=42)
        t1 = time.time()
        mask_gen_time = t1 - t0
        logger.info(f"Mask generation completed in {mask_gen_time:.2f}s")

        # Step 4: Save Mask
        mask_path = DATA_DERIVED_DIR / f"mask_r{pilot_config['realization_id']}_f{int(pilot_config['gap_fraction']*100)}.fits"
        save_mask_to_fits_wrapper(mask_data, mask_path, pilot_config['realization_id'], pilot_config['gap_fraction'])
        logger.info(f"Mask saved to {mask_path}")

        # Step 5: Apply Gap Filling Algorithm
        algo_name = pilot_config['algorithm']
        logger.info(f"Applying {algo_name} algorithm...")
        t0 = time.time()

        if algo_name == "harmonic_interp":
            filled_map = apply_harmonic_filling(map_data, mask_data)
        else:
            raise ValueError(f"Algorithm {algo_name} not supported in pilot.")

        t1 = time.time()
        algo_time = t1 - t0
        logger.info(f"Gap filling completed in {algo_time:.2f}s")

        # Step 6: Compute Power Spectrum
        logger.info("Computing power spectrum...")
        t0 = time.time()
        cls = compute_power_spectrum(filled_map, N_SIDE)
        t1 = time.time()
        ps_time = t1 - t0
        logger.info(f"Power spectrum computation completed in {ps_time:.2f}s")

        # Step 7: Calculate Total Time
        total_time = time.time() - start_time

        # Prepare Log Data
        pilot_log = {
            "timestamp": datetime.now().isoformat(),
            "config": pilot_config,
            "timings": {
                "map_generation_sec": round(gen_time, 3),
                "mask_generation_sec": round(mask_gen_time, 3),
                "gap_filling_sec": round(algo_time, 3),
                "power_spectrum_sec": round(ps_time, 3),
                "total_pilot_time_sec": round(total_time, 3)
            },
            "status": "success",
            "message": "Pilot run completed successfully."
        }

        # Save Log
        log_path = DATA_RESULTS_DIR / "pilot_log.json"
        with open(log_path, 'w') as f:
            json.dump(pilot_log, f, indent=2)

        logger.info(f"Pilot log saved to {log_path}")
        logger.info(f"Total pilot execution time: {total_time:.2f} seconds")

        return pilot_log

    except Exception as e:
        logger.error(f"Pilot run failed: {str(e)}", exc_info=True)
        total_time = time.time() - start_time
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "config": pilot_config,
            "status": "failed",
            "error": str(e),
            "total_time_sec": round(total_time, 3)
        }
        log_path = DATA_RESULTS_DIR / "pilot_log.json"
        with open(log_path, 'w') as f:
            json.dump(error_log, f, indent=2)
        raise e

def main():
    """Entry point for the pilot runner."""
    ensure_directories()
    run_pilot()
    logger.info("Pilot run finished.")

if __name__ == "__main__":
    main()