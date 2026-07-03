import os
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import logging
import sys

# Import logging infrastructure from project
from code.logger import get_logger

# Import models if needed for typing or data handling
from code.models import IonPair, CalculationResult

logger = get_logger(__name__)

# Constants for retry logic
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

def _run_psi4_command(input_path: Path, output_path: Path, work_dir: Path) -> Tuple[int, str]:
    """
    Executes the psi4 command for a single input file.
    
    Args:
        input_path: Path to the .com or .inp file
        output_path: Path where the output will be written
        work_dir: Working directory for the calculation
        
    Returns:
        Tuple of (return_code, stderr_output)
    """
    # Construct command: psi4 input_file output_file
    # Note: psi4 CLI typically redirects stdout to the output file automatically
    # but we explicitly pass the output file name to ensure it goes to the right place.
    cmd = [
        "psi4",
        str(input_path),
        str(output_path)
    ]

    try:
        # Run the process
        result = subprocess.run(
            cmd,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3600  # 1 hour timeout per job
        )
        return result.returncode, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Psi4 calculation timed out: {input_path}")
        return 1, "TimeoutExpired"
    except FileNotFoundError:
        logger.error(f"Psi4 executable not found in PATH: {input_path}")
        return 1, "ExecutableNotFound"
    except Exception as e:
        logger.error(f"Unexpected error running Psi4 for {input_path}: {e}")
        return 1, str(e)

def run_psi4_single(
    ion_pair: IonPair,
    input_dir: Path,
    output_dir: Path,
    max_retries: int = MAX_RETRIES
) -> Optional[CalculationResult]:
    """
    Runs a single Psi4 calculation for an ion pair with retry logic.
    
    This function attempts to run the calculation up to max_retries times.
    If the calculation fails (non-zero return code), it waits and retries.
    
    Args:
        ion_pair: The IonPair object containing geometry and metadata
        input_dir: Directory containing the input files (or where they are generated)
        output_dir: Directory where output files should be written
        max_retries: Maximum number of attempts (default: 3)
        
    Returns:
        CalculationResult object if successful, None if all retries fail.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine input file path. Assuming input files are named <pair_id>.com
    input_file_name = f"{ion_pair.pair_id}.com"
    input_path = input_dir / input_file_name
    output_file_name = f"{ion_pair.pair_id}.out"
    output_path = output_dir / output_file_name

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return None

    attempt = 0
    last_error = "No attempt made"

    while attempt < max_retries:
        attempt += 1
        logger.info(f"Attempting Psi4 calculation for {ion_pair.pair_id} (Attempt {attempt}/{max_retries})")
        
        return_code, stderr_output = _run_psi4_command(input_path, output_path, input_dir)

        if return_code == 0:
            logger.info(f"Successfully completed Psi4 calculation for {ion_pair.pair_id}")
            # Assuming the output file contains the result we need
            # In a full implementation, we would parse the output here
            # For now, we return a placeholder result indicating success
            # The actual parsing is handled by analyze_energies.py
            return CalculationResult(
                pair_id=ion_pair.pair_id,
                status="success",
                output_path=str(output_path),
                error=None
            )
        
        logger.warning(f"Attempt {attempt} failed for {ion_pair.pair_id}: {stderr_output[:200]}")
        last_error = stderr_output

        if attempt < max_retries:
            logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
            time.sleep(RETRY_DELAY_SECONDS)

    logger.error(f"All {max_retries} attempts failed for {ion_pair.pair_id}. Last error: {last_error}")
    return None

def run_psi4_batch(
    ion_pairs: List[IonPair],
    input_dir: Path,
    output_dir: Path,
    max_retries: int = MAX_RETRIES
) -> List[CalculationResult]:
    """
    Runs Psi4 calculations for a batch of ion pairs with retry logic.
    
    Args:
        ion_pairs: List of IonPair objects
        input_dir: Directory containing input files
        output_dir: Directory for output files
        max_retries: Maximum retries per job
        
    Returns:
        List of CalculationResult objects (success or failure records)
    """
    results = []
    failed_pairs = []

    for pair in ion_pairs:
        result = run_psi4_single(pair, input_dir, output_dir, max_retries)
        if result:
            results.append(result)
        else:
            # Record a failure result
            results.append(CalculationResult(
                pair_id=pair.pair_id,
                status="failed",
                output_path=None,
                error="Max retries exceeded"
            ))
            failed_pairs.append(pair.pair_id)

    if failed_pairs:
        logger.error(f"Batch calculation failed for {len(failed_pairs)} pairs: {failed_pairs}")
    else:
        logger.info(f"Batch calculation completed successfully for {len(ion_pairs)} pairs.")

    return results

def main():
    """
    Main entry point for running Psi4 calculations.
    This is a demonstration of how to invoke the batch runner.
    """
    logger.info("Starting Psi4 batch execution (T014 - Retry Logic Implementation)")
    
    # Example usage:
    # In a real scenario, this would load ion pairs from data/IL-Benchmark-local.zip
    # and process them.
    
    # For now, we log that the module is ready and the retry logic is in place.
    logger.info("Retry logic implemented: Up to 3 attempts with 5s delay.")
    logger.info("Ready to process ion pairs from data directory.")

if __name__ == "__main__":
    main()