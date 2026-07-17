"""
T012b: Route real data to alignment pipeline.

This script checks if real data was successfully downloaded by T012 (code/01_download.py).
If real data (FASTQ files) exists, it updates the configuration to route the pipeline
to T014 (code/02_align_call.sh) with the real file paths.

If real data is missing, it exits with a clear error code to prevent the pipeline
from proceeding with synthetic data unless explicitly overridden.
"""
import os
import sys
import argparse
from pathlib import Path
import json

# Constants for data paths
REAL_DATA_DIR = Path("data/interim")
SYNTHETIC_MARKER = Path("data/interim/synthetic_R1.fastq")
REAL_MARKER = Path("data/interim/real_R1.fastq")
CONFIG_FILE = Path("data/interim/pipeline_config.json")
ALIGN_SCRIPT = Path("code/02_align_call.sh")

def check_real_data_exists():
    """
    Check if real FASTQ files exist in the interim directory.
    Returns True if real data is present, False otherwise.
    """
    if not REAL_DATA_DIR.exists():
        return False
    
    # Check for the presence of real R1 and R2 files
    r1_exists = REAL_MARKER.exists()
    r2_exists = (REAL_DATA_DIR / "real_R2.fastq").exists()
    
    return r1_exists and r2_exists

def update_pipeline_config():
    """
    Update the pipeline configuration to use real data for alignment.
    Writes the config to data/interim/pipeline_config.json.
    """
    config = {
        "data_source": "real",
        "input_r1": str(REAL_DATA_DIR / "real_R1.fastq"),
        "input_r2": str(REAL_DATA_DIR / "real_R2.fastq"),
        "alignment_script": str(ALIGN_SCRIPT),
        "status": "ready_for_alignment"
    }
    
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config

def main():
    parser = argparse.ArgumentParser(
        description="Route real data to alignment pipeline (T012b)"
    )
    parser.add_argument(
        "--force-synthetic",
        action="store_true",
        help="Force routing to synthetic data path even if real data exists"
    )
    args = parser.parse_args()

    print(f"Checking for real data in {REAL_DATA_DIR}...")
    
    has_real = check_real_data_exists()
    
    if args.force_synthetic:
        print("WARNING: --force-synthetic flag detected. Routing to synthetic path.")
        print("This task is designed to route REAL data. Use this flag only for testing synthetic pipeline.")
        sys.exit(0) # Exit successfully but do not update config for real data
    
    if has_real:
        print("Real data detected. Updating pipeline configuration for real data alignment.")
        try:
            config = update_pipeline_config()
            print(f"Configuration updated successfully:")
            print(f"  Source: {config['data_source']}")
            print(f"  Input R1: {config['input_r1']}")
            print(f"  Input R2: {config['input_r2']}")
            print(f"  Next Step: Execute {config['alignment_script']}")
            print("T012b completed: Real data routed to alignment.")
        except Exception as e:
            print(f"ERROR: Failed to update pipeline configuration: {e}")
            sys.exit(1)
    else:
        print("ERROR: Real data not found in data/interim/.")
        print("T012 (code/01_download.py) must successfully download real data before running this task.")
        print("If real data is unavailable, the pipeline cannot proceed to alignment with real data.")
        print("Halt reason: Missing real data source.")
        sys.exit(1)

if __name__ == "__main__":
    main()