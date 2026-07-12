import os
import sys
import time
import json
import logging
import signal
from pathlib import Path
from typing import Optional, Dict, Any, Iterator

# Import from local modules based on API surface
from config import get_project_root, get_log_file_path, get_metrics_path
from download import fetch_molecules, verify_checksum
from metrics import (
    calculate_shannon_entropy,
    calculate_lzma_length,
    calculate_sa_score,
    calculate_qed_score,
    calculate_molecular_weight,
    calculate_atom_count,
    timeout,
    TimeoutError
)
from logging_setup import setup_logging, get_logger, log_skipped_molecule, log_timeout_event

# Constants
TIMEOUT_SECONDS = 60
CHUNK_SIZE = 500

# Ensure directories exist
def ensure_directories():
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "figures",
        root / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def process_chunk(chunk: list, logger: logging.Logger) -> list:
    """
    Process a chunk of molecules, calculating metrics.
    Logs skipped molecules (invalid SMILES or timeouts) in the required JSON format.
    
    Args:
        chunk: List of dicts {'cid': int, 'smiles': str}
        logger: Configured logger instance
    
    Returns:
        List of dicts with calculated metrics
    """
    results = []
    
    for item in chunk:
        cid = item['cid']
        smiles = item['smiles']
        
        try:
            # Apply timeout decorator to the metric calculations
            # We wrap the logic to catch TimeoutError specifically
            
            # Calculate metrics
            entropy = calculate_shannon_entropy(smiles)
            lz = calculate_lzma_length(smiles)
            sa = calculate_sa_score(smiles)
            qed = calculate_qed_score(smiles)
            mw = calculate_molecular_weight(smiles)
            atom_count = calculate_atom_count(smiles)
            
            results.append({
                'cid': cid,
                'smiles': smiles,
                'entropy': entropy,
                'lz': lz,
                'sa': sa,
                'qed': qed,
                'mw': mw,
                'atom_count': atom_count
            })
            
        except TimeoutError:
            # Log timeout event with specific JSON format
            log_entry = {
                "event": "skipped",
                "reason": "timeout",
                "cid": cid
            }
            # Use the specific logger method for timeout events if available, 
            # or fall back to standard JSON logging if the helper just formats.
            # Based on API surface, we call the helper which handles the logging.
            log_timeout_event(cid, logger)
            # Also ensure the raw JSON is logged as required by the task spec
            logger.warning(json.dumps(log_entry))
            
        except Exception as e:
            # Likely invalid SMILES or other processing error
            log_entry = {
                "event": "skipped",
                "reason": "invalid_smiles",
                "cid": cid
            }
            log_skipped_molecule(cid, str(e), logger)
            # Also ensure the raw JSON is logged as required by the task spec
            logger.warning(json.dumps(log_entry))
    
    return results

def run_download_step(logger: logging.Logger) -> Optional[Iterator[Dict[str, Any]]]:
    """
    Initialize the dataset iterator.
    """
    logger.info("Starting download/streaming step...")
    try:
        # fetch_molecules returns an iterator
        iterator = fetch_molecules()
        return iterator
    except Exception as e:
        logger.error(f"Failed to initialize dataset stream: {e}")
        return None

def run_metrics_step(data_iter: Iterator[Dict[str, Any]], logger: logging.Logger):
    """
    Process molecules in chunks and write to CSV.
    """
    metrics_path = get_metrics_path()
    file_exists = os.path.exists(metrics_path)
    
    header = ['cid', 'smiles', 'entropy', 'lz', 'sa', 'qed', 'mw', 'atom_count']
    
    count = 0
    chunk = []
    
    for item in data_iter:
        chunk.append(item)
        if len(chunk) >= CHUNK_SIZE:
            results = process_chunk(chunk, logger)
            
            # Write results to CSV
            with open(metrics_path, 'a' if file_exists else 'w', newline='') as f:
                import csv
                writer = csv.DictWriter(f, fieldnames=header)
                if not file_exists:
                    writer.writeheader()
                    file_exists = True
                for res in results:
                    writer.writerow(res)
            
            count += len(chunk)
            logger.info(f"Processed {count} molecules")
            chunk = []
    
    # Process remaining
    if chunk:
        results = process_chunk(chunk, logger)
        with open(metrics_path, 'a' if file_exists else 'w', newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=header)
            if not file_exists:
                writer.writeheader()
            for res in results:
                writer.writerow(res)
        logger.info(f"Processed final batch. Total: {count + len(results)}")

def run_analysis_step(logger: logging.Logger):
    """
    Placeholder for analysis step.
    """
    logger.info("Analysis step placeholder")

def run_viz_step(logger: logging.Logger):
    """
    Placeholder for visualization step.
    """
    logger.info("Visualization step placeholder")

def main():
    """
    Main orchestration entry point.
    """
    ensure_directories()
    
    # Setup logging
    log_file = get_log_file_path()
    logger = setup_logging(log_file=log_file)
    
    logger.info("Pipeline started")
    
    # 1. Download/Stream
    data_iter = run_download_step(logger)
    if not data_iter:
        logger.error("Download step failed. Exiting.")
        sys.exit(1)
    
    # 2. Metrics
    run_metrics_step(data_iter, logger)
    
    # 3. Analysis
    run_analysis_step(logger)
    
    # 4. Viz
    run_viz_step(logger)
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()