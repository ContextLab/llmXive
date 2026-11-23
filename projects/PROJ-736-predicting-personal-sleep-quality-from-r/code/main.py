"""Main orchestration script for the sleep quality prediction pipeline."""
import os
import sys
import json
import time
from pathlib import Path
from config import get_paths, ensure_dirs

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.download_hcp import download_hcp_data, main as download_main
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from utils.logging import (
    log_stage_start, 
    log_stage_complete, 
    log_stage_error, 
    setup_logging,
    compute_sha256
)


def run_pipeline() -> bool:
    """Run the full data pipeline: download -> preprocess -> feature engineering."""
    paths = get_paths()
    log_dir = paths["logs"]
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pipeline_run.json")
    
    # Setup logging
    setup_logging(log_file)
    log_stage_start("full_pipeline")
    
    success = True
    
    # Step 1: Download HCP data
    log_stage_start("Download HCP Data")
    if not download_hcp_data():
        log_stage_error("Download HCP Data", "Failed to download HCP data")
        success = False
    else:
        log_stage_complete("Download HCP Data")
    
    if not success:
        log_stage_complete("full_pipeline", {"status": "failed", "stage": "download"})
        return False
    
    # Step 2: Preprocess data
    log_stage_start("Preprocessing")
    if not preprocess_main():
        log_stage_error("Preprocessing", "Failed to preprocess data")
        success = False
    else:
        log_stage_complete("Preprocessing")
    
    if not success:
        log_stage_complete("full_pipeline", {"status": "failed", "stage": "preprocessing"})
        return False
    
    # Step 3: Feature engineering (T014c)
    log_stage_start("Feature Engineering")
    if not feature_main():
        log_stage_error("Feature Engineering", "Failed to compute features")
        success = False
    else:
        log_stage_complete("Feature Engineering")
    
    # T043: Add checksum verification for intermediate .npy files
    # Compute and log SHA256 hashes for all generated connectivity vectors
    if success:
        processed_dir = paths["processed"]
        npy_files = [f for f in os.listdir(processed_dir) if f.endswith('.npy')]
        
        checksums = {}
        for npy_file in npy_files:
            file_path = os.path.join(processed_dir, npy_file)
            try:
                file_hash = compute_sha256(file_path)
                checksums[npy_file] = file_hash
                log_stage_start("Checksum Verification", {
                    "file": npy_file, 
                    "sha256": file_hash
                })
            except Exception as e:
                log_stage_error("Checksum Verification", f"Failed to hash {npy_file}: {str(e)}")
                success = False
        
        # Log summary of checksums
        log_stage_complete("Checksum Verification", {
            "total_files": len(npy_files),
            "verified": len(checksums),
            "checksums": checksums
        })

    if success:
        log_stage_complete("full_pipeline", {"status": "success"})
    else:
        log_stage_complete("full_pipeline", {"status": "failed", "stage": "feature_engineering"})
            
    return success


def main() -> bool:
    """Main entry point."""
    success = run_pipeline()
    return success



if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)