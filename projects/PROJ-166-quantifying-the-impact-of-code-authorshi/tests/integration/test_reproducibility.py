import os
import sys
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
import subprocess
import pytest
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import ensure_directories
from analysis.fit_models import main as run_fit_models
from analysis.robustness import main as run_robustness

# Setup logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_pipeline_run():
    """
    Execute the analysis pipeline steps required to generate the output files.
    This function calls the main entry points of the analysis scripts directly.
    """
    ensure_directories()
    
    # Check prerequisites
    input_files = [
        "data/processed/repo_metrics_clean.csv",
        "data/processed/robustness_subsample_pvalues.csv",
        "data/processed/robustness_entropy_pvalues.csv",
        "data/processed/robustness_lagged_results.json"
    ]
    
    for inp in input_files:
        if not Path(inp).exists():
            raise FileNotFoundError(f"Required input file missing for reproducibility test: {inp}")
    
    logger.info("Running fit_models.py...")
    # Run the model fitting script
    run_fit_models()
    
    logger.info("Running robustness.py...")
    # Run the robustness analysis script
    run_robustness()
    
    # Verify outputs were created
    output_files = [
        "data/processed/model_results_raw.json",
        "data/processed/robustness_results.json"
    ]
    
    for out in output_files:
        if not Path(out).exists():
            raise FileNotFoundError(f"Output file missing after pipeline run: {out}")
    
    return output_files

@pytest.mark.integration
def test_reproducibility():
    """
    Test that running the pipeline twice on the same seed dataset produces
    byte-for-byte identical results (within floating-point tolerance).
    
    This verifies SC-003 (Reproducibility).
    """
    ensure_directories()
    
    files_to_check = [
        "data/processed/model_results_raw.json",
        "data/processed/robustness_results.json"
    ]
    
    # --- Run 1 ---
    logger.info("=== Starting Pipeline Run 1 ===")
    try:
        run_pipeline_run()
    except Exception as e:
        pytest.fail(f"Pipeline Run 1 failed: {str(e)}")
    
    hashes_run1 = {}
    for f in files_to_check:
        if not Path(f).exists():
            raise FileNotFoundError(f"Output file missing after Run 1: {f}")
        hashes_run1[f] = get_file_hash(f)
    
    # --- Run 2 ---
    logger.info("=== Starting Pipeline Run 2 ===")
    try:
        run_pipeline_run()
    except Exception as e:
        pytest.fail(f"Pipeline Run 2 failed: {str(e)}")
    
    hashes_run2 = {}
    for f in files_to_check:
        if not Path(f).exists():
            raise FileNotFoundError(f"Output file missing after Run 2: {f}")
        hashes_run2[f] = get_file_hash(f)
    
    # --- Compare ---
    all_match = True
    for f in files_to_check:
        if hashes_run1[f] != hashes_run2[f]:
            logger.warning(f"Hash mismatch for {f}. Attempting float comparison...")
            try:
                with open(f, 'r') as file:
                    data1 = json.load(file)
                
                # We cannot re-read the file differently to get data2, 
                # but since the file is the same object in disk, we must compare 
                # the content of the file we just read against itself? 
                # No, the issue is that the file content changed between runs? 
                # Wait, the file on disk IS the result of Run 2. 
                # We need to compare Run 1 result (which we hashed) vs Run 2 result (file on disk).
                # Since we deleted/moved the Run 1 file? No, we overwrote it.
                # To do this properly without moving files, we should have loaded data1 into memory.
                
                # Let's re-load data1 from the hash? No.
                # We need to modify the logic: Load data1 into memory before Run 2.
                pass 
            except json.JSONDecodeError:
                logger.error(f"Files differ and are not JSON: {f}")
                all_match = False
                continue
    
    # Proper comparison logic: Load Run 1 data into memory, Run 2, compare in memory.
    logger.info("=== Re-evaluating with in-memory comparison ===")
    
    # Re-run Run 1 and load data
    logger.info("Run 1 (Memory Capture)")
    run_pipeline_run()
    data_run1 = {}
    for f in files_to_check:
        with open(f, 'r') as file:
            data_run1[f] = json.load(file)
    
    # Re-run Run 2
    logger.info("Run 2 (Comparison)")
    run_pipeline_run()
    data_run2 = {}
    for f in files_to_check:
        with open(f, 'r') as file:
            data_run2[f] = json.load(file)
    
    # Compare in-memory objects
    for f in files_to_check:
        if data_run1[f] != data_run2[f]:
            logger.error(f"Content mismatch in {f} between Run 1 and Run 2.")
            logger.error(f"Run 1: {data_run1[f]}")
            logger.error(f"Run 2: {data_run2[f]}")
            assert False, f"Reproducibility failed: {f} differs between runs."
    
    logger.info("Reproducibility test PASSED: Outputs are identical.")
    assert True

if __name__ == "__main__":
    test_reproducibility()