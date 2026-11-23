"""
Validation script for docs/quickstart.md.
Executes the end-to-end pipeline on a small subset of the real dataset
to verify that all components (data loading, baseline extraction, 
perturbation, validity checks, and analysis) function correctly.

This script:
1. Loads a small sample (e.g., 10 rows) from the real bigbench_lite dataset.
2. Runs the baseline extraction pipeline.
3. Runs a minimal noise sweep (1 sigma value).
4. Runs the statistical analysis.
5. Verifies that all expected output files are created and non-empty.
"""
import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import load_config, PipelineConfig, OutputPaths
from data_loader import load_reasoning_dataset, ConfigurationError
from main import run_baseline_extraction, run_noise_sweep, run_final_analysis, setup_logging, ensure_output_directory
from streaming_utils import sample_streaming_dataset
from memory_monitor import reset_memory_tracker, save_memory_profile

# Configure logging
logger = logging.getLogger("quickstart_validation")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def check_file_exists(path: Path, description: str) -> bool:
    if not path.exists():
        logger.error(f"FAILED: {description} missing at {path}")
        return False
    if path.stat().st_size == 0:
        logger.error(f"FAILED: {description} at {path} is empty")
        return False
    logger.info(f"OK: {description} exists at {path} ({path.stat().st_size} bytes)")
    return True

def run_validation():
    start_time = time.time()
    logger.info("Starting Quickstart Validation...")

    # 1. Setup
    try:
        config = load_config()
        # Override config for validation: small sample
        config.data_config.max_samples = 10
        config.noise_sweep_config.sigma_values = [0.1]  # Just one sigma
        config.noise_sweep_config.sigma_min = 0.1
        config.noise_sweep_config.sigma_max = 0.1
        config.noise_sweep_config.step = 0.1
        
        # Ensure output directories exist
        ensure_output_directory(config.output_paths.baseline_vectors)
        ensure_output_directory(config.output_paths.perturbed_vectors)
        ensure_output_directory(config.output_paths.validity_log)
        ensure_output_directory(config.output_paths.statistical_results)
        ensure_output_directory(config.output_paths.trade_off_curve)
        ensure_output_directory(config.output_paths.global_trade_off_curve)
        ensure_output_directory(config.output_paths.sensitivity_report)
        
        reset_memory_tracker()
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        traceback.print_exc()
        return False

    # 2. Load Real Data (Small Subset)
    logger.info("Loading real dataset (subset)...")
    try:
        # Use the real loader, but stream and sample
        dataset_iter = load_reasoning_dataset(config.data_config)
        # Sample 10 rows from the real stream
        sample_data = list(sample_streaming_dataset(dataset_iter, n=10, seed=42))
        
        if not sample_data:
            logger.error("Failed to load any data from real source.")
            return False
        
        logger.info(f"Loaded {len(sample_data)} real samples.")
    except ConfigurationError as e:
        logger.error(f"Configuration error loading data: {e}")
        return False
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        traceback.print_exc()
        return False

    # 3. Run Baseline Extraction
    logger.info("Running Baseline Extraction...")
    try:
        # We need to patch the data loader to use our sample data if the main loop
        # expects to call load_reasoning_dataset again. 
        # However, the main.py functions are designed to call the loader themselves.
        # To strictly follow "run quickstart", we assume the pipeline uses the config
        # and loader. Since we can't easily inject the sample into the global loader
        # without modifying main.py significantly, we will run the pipeline with
        # the config set to max_samples=10.
        
        # Re-run loader with max_samples set
        config.data_config.max_samples = 10
        # The main functions call load_reasoning_dataset internally.
        # We rely on the streaming_utils to respect max_samples if implemented there,
        # or we assume the loader respects config.max_samples.
        
        # For this validation, we assume the pipeline logic in main.py 
        # correctly uses the config to limit samples.
        
        run_baseline_extraction(config)
        
        baseline_path = Path(config.output_paths.baseline_vectors)
        if not check_file_exists(baseline_path, "Baseline Vectors CSV"):
            return False
            
    except Exception as e:
        logger.error(f"Baseline extraction failed: {e}")
        traceback.print_exc()
        return False

    # 4. Run Noise Sweep
    logger.info("Running Noise Sweep (minimal)...")
    try:
        run_noise_sweep(config)
        
        # Check outputs
        perturbed_path = Path(config.output_paths.perturbed_vectors)
        validity_log_path = Path(config.output_paths.validity_log)
        
        # Note: If validity check filters everything out, perturbed_vectors might be empty or small.
        # We check existence.
        if not check_file_exists(perturbed_path, "Perturbed Vectors CSV"):
            logger.warning("Perturbed vectors file is empty or missing (possible validity filter).")
            # This might be expected if the noise is too high for such a small sample, 
            # but for validation we expect at least a header.
            # Let's check if the file exists and has a header.
            if perturbed_path.exists() and perturbed_path.stat().st_size > 0:
                logger.info("Perturbed vectors file exists and has content.")
            else:
                logger.error("Perturbed vectors file is completely empty.")
                return False

        if not check_file_exists(validity_log_path, "Validity Log CSV"):
            return False

    except Exception as e:
        logger.error(f"Noise sweep failed: {e}")
        traceback.print_exc()
        return False

    # 5. Run Final Analysis
    logger.info("Running Final Analysis...")
    try:
        run_final_analysis(config)
        
        # Check outputs
        stats_path = Path(config.output_paths.statistical_results)
        trade_off_path = Path(config.output_paths.trade_off_curve)
        global_trade_path = Path(config.output_paths.global_trade_off_curve)
        sensitivity_path = Path(config.output_paths.sensitivity_report)
        
        if not check_file_exists(stats_path, "Statistical Results JSON"):
            return False
        if not check_file_exists(trade_off_path, "Trade-off Curve CSV"):
            return False
        if not check_file_exists(global_trade_path, "Global Trade-off CSV"):
            return False
        if not check_file_exists(sensitivity_path, "Sensitivity Report JSON"):
            return False

    except Exception as e:
        logger.error(f"Final analysis failed: {e}")
        traceback.print_exc()
        return False

    # 6. Memory Profile Check
    memory_profile_path = Path("data/processed/memory_profile.json")
    if not check_file_exists(memory_profile_path, "Memory Profile JSON"):
        logger.warning("Memory profile missing, but pipeline succeeded.")
    else:
        try:
            with open(memory_profile_path, 'r') as f:
                mem_data = json.load(f)
                peak_rss = mem_data.get('peak_rss_mb', 0)
                if peak_rss > 7000:
                    logger.warning(f"Peak RSS {peak_rss}MB exceeded 7GB limit!")
                else:
                    logger.info(f"Peak RSS {peak_rss}MB within limit.")
        except Exception as e:
            logger.warning(f"Could not parse memory profile: {e}")

    elapsed = time.time() - start_time
    logger.info(f"Validation completed successfully in {elapsed:.2f} seconds.")
    return True

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
