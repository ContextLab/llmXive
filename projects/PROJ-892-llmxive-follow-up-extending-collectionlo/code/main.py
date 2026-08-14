import os
import sys
import json
import csv
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/pipeline.log')
    ]
)
logger = logging.getLogger('main')

# Ensure state directory exists
STATE_DIR = Path('state')
STATE_DIR.mkdir(exist_ok=True)

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

RESULTS_CSV = DATA_DIR / 'results.csv'
ANALYSIS_RESULTS_JSON = DATA_DIR / 'analysis_results.json'


def handle_oom(error: Exception) -> bool:
    """
    Handle Out Of Memory errors.
    Returns True if the error was handled (skipped), False if it should crash.
    """
    if isinstance(error, MemoryError) or (hasattr(error, 'code') and error.code == 137):
        logger.warning("Quantization Failure: OOM detected. Skipping affected quantization level.")
        return True
    return False


def run_fp16_generation() -> None:
    """
    Execute the FP16 baseline generation pipeline.
    Delegates to the generator module logic.
    """
    logger.info("Starting FP16 baseline generation...")
    # This function would typically orchestrate calls to generator.py
    # and metrics.py to generate baseline images and compute initial metrics.
    # For this task, we assume the heavy lifting is done by run_statistical_analysis
    # or previous tasks, but we ensure the path exists for completeness.
    try:
        from generator import generate_fp16_baseline_images, generate_fp16_reference_images
        # Trigger generation if not already done
        generate_fp16_baseline_images()
        generate_fp16_reference_images()
        logger.info("FP16 baseline generation completed.")
    except Exception as e:
        if handle_oom(e):
            logger.error("FP16 generation skipped due to OOM.")
        else:
            raise


def run_quantized_generation() -> None:
    """
    Execute the quantized (INT8/INT4) generation pipeline.
    """
    logger.info("Starting quantized generation...")
    try:
        from generator import generate_images_for_adapters
        from data_loader import apply_quantization
        # Ensure quantization is applied if not done
        # apply_quantization() # Assuming this is called in T016/T020
        generate_images_for_adapters()
        logger.info("Quantized generation completed.")
    except Exception as e:
        if handle_oom(e):
            logger.error("Quantized generation skipped due to OOM.")
        else:
            raise


def save_results_to_csv(results: list) -> None:
    """
    Save the collected metrics results to data/results.csv.
    """
    if not results:
        logger.warning("No results to save.")
        return

    fieldnames = results[0].keys()
    with open(RESULTS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Results saved to {RESULTS_CSV}")


def run_statistical_analysis() -> Dict[str, Any]:
    """
    Execute the Bayesian statistical analysis script and save results.
    This task (T027) specifically implements the logic to:
    1. Execute the analysis script (statistical_analysis.py).
    2. Ensure the output file (data/analysis_results.json) is written.
    """
    logger.info("Executing statistical analysis...")
    
    # Import the main function from statistical_analysis
    # This function is expected to perform the Bayesian Hierarchical Model
    # and write the results to ANALYSIS_RESULTS_JSON directly.
    try:
        from statistical_analysis import main as analysis_main
        
        # Run the analysis. The main function in statistical_analysis.py
        # is responsible for loading data, running the model, and saving the JSON.
        # We call it here to trigger the execution flow.
        analysis_main()
        
        # Verify the output file exists
        if not ANALYSIS_RESULTS_JSON.exists():
            logger.error(f"Statistical analysis failed to produce {ANALYSIS_RESULTS_JSON}")
            # We do not raise here immediately, as the analysis_main might have failed silently
            # or logged the error. We check the file existence as the primary success criterion.
            return {}
        
        # Load and return the results for potential further processing or logging
        with open(ANALYSIS_RESULTS_JSON, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        logger.info(f"Statistical analysis completed. Results saved to {ANALYSIS_RESULTS_JSON}")
        return results

    except ImportError as e:
        logger.error(f"Failed to import statistical analysis module: {e}")
        raise
    except Exception as e:
        logger.error(f"Statistical analysis failed with error: {e}")
        raise


def main() -> None:
    """
    Main entry point for the pipeline.
    Orchestrates the full flow or specific stages as needed.
    For T027, the focus is on ensuring the statistical analysis runs and saves results.
    """
    logger.info("Pipeline main started.")
    
    try:
        # 1. Run FP16 Generation (if not done)
        # run_fp16_generation() 
        
        # 2. Run Quantized Generation (if not done)
        # run_quantized_generation()
        
        # 3. Run Statistical Analysis (The core of T027)
        results = run_statistical_analysis()
        
        if results:
            logger.info("Analysis pipeline successful.")
            print(json.dumps(results, indent=2))
        else:
            logger.warning("Analysis pipeline completed but returned no results.")
            
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Pipeline main finished.")


if __name__ == "__main__":
    main()