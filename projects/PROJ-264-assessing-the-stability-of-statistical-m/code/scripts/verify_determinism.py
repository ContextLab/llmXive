import hashlib
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils import set_seed, setup_logging
from code.scripts.run_smoke_test import main as run_smoke_test
from code.config import RESULTS_DIR

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Set up a logger that writes to both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_pipeline_run(run_id: int, seed: int, results_dir: Path) -> None:
    """Run the smoke test pipeline with a specific seed and store results in a subdirectory."""
    # Create a temporary directory for this run
    run_dir = results_dir / f"run_{run_id}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    
    # Temporarily redirect results to this run directory
    original_results_dir = RESULTS_DIR
    
    # We need to monkey-patch the config or ensure the smoke test writes to the right place
    # Since we can't easily change config, we'll run the smoke test and then move files
    # Actually, let's just run the smoke test normally, but we need to ensure it uses the seed
    
    # Set the seed globally
    set_seed(seed)
    
    # Run the smoke test (this will write to the default RESULTS_DIR)
    # We need to clear the default results dir first to avoid mixing runs
    if results_dir.exists():
        for f in results_dir.glob("*.csv"):
            f.unlink()
        for f in results_dir.glob("*.md"):
            f.unlink()
    
    # Run the smoke test
    try:
        run_smoke_test()
    except Exception as e:
        logging.error(f"Smoke test failed in run {run_id}: {e}")
        raise
    
    # Move the generated files to the run-specific directory
    expected_files = [
        "raw_evaluations.csv",
        "stability_metrics.csv",
        "correlation_results.csv",
        "permutation_results.csv",
        "final_report.md"
    ]
    
    for filename in expected_files:
        src = results_dir / filename
        if src.exists():
            shutil.move(str(src), str(run_dir / filename))
        else:
            logging.warning(f"Expected file {filename} not found for run {run_id}")

def compare_checksums(run1_dir: Path, run2_dir: Path, expected_files: List[str]) -> Tuple[bool, Dict[str, Tuple[str, str]]]:
    """Compare checksums of files between two runs."""
    mismatches = {}
    all_match = True
    
    for filename in expected_files:
        file1 = run1_dir / filename
        file2 = run2_dir / filename
        
        if not file1.exists() or not file2.exists():
            logging.error(f"Missing file for comparison: {filename}")
            all_match = False
            continue
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        if hash1 != hash2:
            mismatches[filename] = (hash1, hash2)
            all_match = False
            logging.error(f"Mismatch in {filename}: {hash1} vs {hash2}")
        else:
            logging.info(f"Match for {filename}: {hash1}")
    
    return all_match, mismatches

def main():
    """Main entry point for determinism verification."""
    logger = setup_logger("determinism_check", "results/determinism_verification.log")
    logger.info("Starting determinism verification...")
    
    # Configuration
    seed = 42  # Fixed seed for reproducibility
    results_dir = Path("results")
    expected_files = [
        "raw_evaluations.csv",
        "stability_metrics.csv",
        "correlation_results.csv",
        "permutation_results.csv",
        "final_report.md"
    ]
    
    # Ensure results directory exists
    results_dir.mkdir(exist_ok=True)
    
    try:
        # Run 1
        logger.info("Running pipeline run #1...")
        run_pipeline_run(1, seed, results_dir)
        logger.info("Run #1 completed.")
        
        # Run 2
        logger.info("Running pipeline run #2...")
        run_pipeline_run(2, seed, results_dir)
        logger.info("Run #2 completed.")
        
        # Compare checksums
        run1_dir = results_dir / "run_1"
        run2_dir = results_dir / "run_2"
        
        logger.info("Comparing checksums...")
        all_match, mismatches = compare_checksums(run1_dir, run2_dir, expected_files)
        
        if all_match:
            logger.info("SUCCESS: All output files are identical across runs. Determinism verified.")
            # Write summary to a dedicated file
            summary_file = results_dir / "determinism_summary.txt"
            with open(summary_file, "w") as f:
                f.write("Determinism Verification Summary\n")
                f.write("=" * 40 + "\n")
                f.write(f"Seed used: {seed}\n")
                f.write(f"Run 1 directory: {run1_dir}\n")
                f.write(f"Run 2 directory: {run2_dir}\n")
                f.write("All output files match perfectly.\n")
                f.write("SHA-256 checksums:\n")
                for filename in expected_files:
                    hash_val = compute_file_hash(run1_dir / filename)
                    f.write(f"  {filename}: {hash_val}\n")
            logger.info(f"Summary written to {summary_file}")
            return 0
        else:
            logger.error("FAILURE: Determinism check failed. Output files differ between runs.")
            # Write failure summary
            summary_file = results_dir / "determinism_summary.txt"
            with open(summary_file, "w") as f:
                f.write("Determinism Verification Summary - FAILED\n")
                f.write("=" * 40 + "\n")
                f.write(f"Seed used: {seed}\n")
                f.write("The following files differ:\n")
                for filename, (h1, h2) in mismatches.items():
                    f.write(f"  {filename}:\n    Run 1: {h1}\n    Run 2: {h2}\n")
            logger.error(f"Failure summary written to {summary_file}")
            return 1
    
    except Exception as e:
        logger.exception(f"Unexpected error during determinism verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())