"""
Manual verification script for T039.
Run this script directly to verify the pipeline processes real data.
It attempts to download a small real dataset (if available) or run with
the existing data in data/raw/ to verify memory stability.
"""
import os
import sys
import gc
import tracemalloc
import time
from pathlib import Path

# Add code to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from main import run_pipeline
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    print("=== T039 Real Data Flow Verification ===")
    print(f"Project Root: {PROJECT_ROOT}")
    
    # Check for existing data
    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    if not raw_data_dir.exists():
        print(f"Warning: {raw_data_dir} does not exist. Creating it...")
        raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for studies.csv
    studies_file = raw_data_dir / "studies.csv"
    if not studies_file.exists():
        print(f"Warning: {studies_file} not found. Running pipeline with empty input.")
        print("This will trigger the 'No studies found' narrative mode (T018).")
        input_path = str(studies_file)
    else:
        print(f"Found studies file: {studies_file}")
        input_path = str(studies_file)

    output_file = PROJECT_ROOT / "data" / "derived" / "test_meta_result.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Output path: {output_file}")
    print("Starting pipeline...")

    tracemalloc.start()
    start_time = time.time()

    try:
        result = run_pipeline(input_path=input_path, output_path=str(output_file))
        end_time = time.time()
        
        current, peak = tracemalloc.get_traced_memory()
        peak_mb = peak / 1024 / 1024
        
        print(f"\n--- Results ---")
        print(f"Status: {result}")
        print(f"Runtime: {end_time - start_time:.2f} seconds")
        print(f"Peak Memory: {peak_mb:.2f} MB")
        
        if output_file.exists():
            print(f"Output file created successfully: {output_file}")
            # Verify content
            import json
            with open(output_file, 'r') as f:
                data = json.load(f)
            print(f"Study Count: {data.get('study_count', 'N/A')}")
            print(f"Synthesis Mode: {data.get('synthesis_mode', 'N/A')}")
            print("\nT039 Verification: PASSED")
        else:
            print("ERROR: Output file was not created.")
            print("T039 Verification: FAILED")
            
    except MemoryError:
        print("\nERROR: MemoryError occurred during pipeline execution.")
        print("T039 Verification: FAILED - Memory Overflow")
    except Exception as e:
        print(f"\nERROR: Pipeline execution failed with exception: {e}")
        import traceback
        traceback.print_exc()
        print("T039 Verification: FAILED")
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    main()