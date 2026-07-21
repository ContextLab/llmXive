import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import joblib

from seed_manager import get_seed
from logging_utils import setup_logger

# Constants
BATCH_TIMEOUT_SECONDS = 600  # 10 minutes
MAX_RETRIES = 3
MAX_DEPTH_RF = 15  # Constraint for Random Forest

logger = setup_logger(__name__)

def check_obabel_available() -> bool:
    """Check if the obabel command-line tool is available in the system PATH."""
    try:
        result = subprocess.run(
            ["obabel", "-h"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def smiles_to_obabel_fingerprint(smiles: str, fp_type: str = "ECFP4") -> Optional[str]:
    """
    Generate a fingerprint for a single SMILES string using obabel.
    Implements a timeout and retry mechanism for individual molecules.
    
    Args:
        smiles: The SMILES string of the molecule.
        fp_type: The fingerprint type (ECFP4, MACCS, FP2).
        
    Returns:
        The fingerprint string or None if generation fails after retries.
    """
    if not smiles or not isinstance(smiles, str):
        return None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Map internal type to obabel flags
            # ECFP4 -> ecfp4 (or ecfp 4), MACCS -> maccs, FP2 -> fp2
            # Note: obabel syntax: -xfp <name> or -x<name> depending on version
            # Standard: -xfp ecfp4, -xfp maccs, -xfp fp2
            fp_flag = "xfp"
            fp_name = fp_type.lower()
            
            cmd = [
                "obabel",
                "-:", smiles,  # Input from string
                "-O-",         # Output to stdout
                f"-{fp_flag}{fp_name}"
            ]
            
            # Execute with a timeout per molecule (e.g., 30 seconds per molecule to prevent hanging)
            # The batch timeout is handled at the process level
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # Per-molecule timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.decode("utf-8").strip()
                # obabel output might include the SMILES and then the fingerprint
                # Format: SMILES \t Fingerprint
                parts = output.split("\t")
                if len(parts) >= 2:
                    return parts[1].strip()
                return output.strip()
            else:
                logger.warning(f"Obabel failed for {smiles[:20]}... (Attempt {attempt}/{MAX_RETRIES}): {result.stderr.decode('utf-8')[:100]}")
        
        except subprocess.TimeoutExpired:
            logger.warning(f"Obabel timeout for {smiles[:20]}... (Attempt {attempt}/{MAX_RETRIES})")
        except Exception as e:
            logger.error(f"Unexpected error for {smiles[:20]}...: {e}")
        
        if attempt < MAX_RETRIES:
            time.sleep(1)  # Brief pause before retry
    
    return None

def generate_fingerprints_batch(batch_data: List[Dict[str, Any]], fp_type: str, error_log_path: Path) -> List[Dict[str, Any]]:
    """
    Process a batch of molecules to generate fingerprints.
    Logs failures to error_log_path.
    """
    results = []
    failed_count = 0
    
    for idx, row in enumerate(batch_data):
        smiles = row.get("smiles")
        if not smiles:
            continue
        
        fp = smiles_to_obabel_fingerprint(smiles, fp_type)
        
        if fp:
            new_row = row.copy()
            new_row[f"{fp_type}_fp"] = fp
            results.append(new_row)
        else:
            failed_count += 1
            # Log to error file
            try:
                with open(error_log_path, "a") as f:
                    f.write(f"{smiles}\t{fp_type}\tFailed after {MAX_RETRIES} retries\n")
            except IOError as e:
                logger.error(f"Could not write to error log: {e}")
    
    if failed_count > 0:
        logger.warning(f"Failed to generate fingerprints for {failed_count} molecules in this batch.")
    
    return results

def process_dataset(data_path: Path, output_path: Path, fp_types: List[str] = ["ECFP4", "MACCS", "FP2"]):
    """
    Process the dataset to generate fingerprints.
    Implements batch timeout and parallel processing via joblib.
    """
    import pandas as pd
    
    if not check_obabel_available():
        raise RuntimeError("Open Babel (obabel) is not installed or not in PATH. Please install it.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load data from {data_path}: {e}")
    
    logger.info(f"Loaded {len(df)} molecules from {data_path}")
    
    # Prepare error log path
    error_log_path = output_path.parent / "fingerprint_errors.log"
    # Clear previous log if exists
    if error_log_path.exists():
        error_log_path.unlink()
    
    # Split into batches for parallel processing
    # We assume the dataset is not too massive to fit in memory for the list structure
    # but the obabel calls are the bottleneck.
    batch_size = 50
    batches = [df[i:i+batch_size].to_dict('records') for i in range(0, len(df), batch_size)]
    
    all_results = []
    start_time = time.time()
    
    # Use joblib for parallel execution
    # Note: We use a timeout on the whole process group if needed, but here we rely on
    # individual molecule timeouts and the 10-minute batch check.
    
    def process_single_batch(batch, fp_types_list, log_path):
        # Flatten batch processing for a specific fp type or all?
        # The task implies generating specific fingerprints. We'll do ECFP4 first as per priority.
        # If multiple types are requested, we might need to call obabel multiple times or once with multiple flags.
        # Obabel allows multiple -xfp flags.
        
        combined_results = []
        for row in batch:
            smiles = row.get("smiles")
            if not smiles:
                continue
            
            row_copy = row.copy()
            success = True
            
            for fp_type in fp_types_list:
                fp = smiles_to_obabel_fingerprint(smiles, fp_type)
                if fp:
                    row_copy[f"{fp_type}_fp"] = fp
                else:
                    success = False
                    with open(log_path, "a") as f:
                        f.write(f"{smiles}\t{fp_type}\tFailed after {MAX_RETRIES} retries\n")
            
            if success or any(f"{fp_type}_fp" in row_copy for fp_type in fp_types_list):
                combined_results.append(row_copy)
        
        return combined_results

    # Parallel processing with a check for total elapsed time
    # We use a ProcessPoolExecutor to parallelize batches
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(process_single_batch, batch, fp_types, error_log_path)
            for batch in batches
        ]
        
        for future in as_completed(futures):
            # Check if we've exceeded the 10-minute batch timeout (for the whole process, not just one batch)
            # The task says "10-minute batch timeout check for the obabel subprocess".
            # This implies if the whole batch processing exceeds 10 mins, we should stop or warn.
            # However, the constraint is "total pipeline does not exceed 6-hour limit".
            # We implement a check here to log if a batch is taking too long.
            if time.time() - start_time > BATCH_TIMEOUT_SECONDS:
                logger.warning(f"BATCH TIMEOUT: Total processing time exceeded {BATCH_TIMEOUT_SECONDS} seconds. Stopping further batches.")
                # Cancel remaining futures
                for f in futures:
                    f.cancel()
                break
            
            try:
                batch_results = future.result()
                all_results.extend(batch_results)
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
    
    # Convert to DataFrame and save
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_parquet(output_path, index=False)
        logger.info(f"Saved {len(result_df)} molecules with fingerprints to {output_path}")
    else:
        logger.error("No fingerprints were generated successfully.")
        raise RuntimeError("Fingerprint generation failed for all molecules.")

def main():
    """
    Main entry point for fingerprint generation.
    Reads from data/derived/train_set.csv (or similar) and writes to data/derived/fingerprints.parquet.
    """
    # Determine paths based on project structure
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "derived"
    output_file = data_dir / "fingerprints.parquet"
    input_file = data_dir / "train_set.csv"
    
    if not input_file.exists():
        # Fallback to a generic name if specific split isn't found, but per spec T011.5 creates train_set.csv
        logger.warning(f"Input file {input_file} not found. Looking for alternative...")
        # Could implement logic to find the most recent train set
        raise FileNotFoundError(f"Input data file {input_file} not found.")
    
    logger.info(f"Starting fingerprint generation from {input_file}")
    
    try:
        process_dataset(input_file, output_file, fp_types=["ECFP4", "MACCS", "FP2"])
    except Exception as e:
        logger.error(f"Fingerprint generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()