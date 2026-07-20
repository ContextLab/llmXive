"""
main.py - Orchestration script for the Zero-Shot Drift Detection pipeline.

This script runs the full scoring pipeline:
1. Validates data integrity (optional, skipped if data is assumed present from previous runs)
2. Builds taxonomy centroids (if not already present)
3. Runs drift scoring on available logs
4. Exports results to CSV

Dependencies:
- T005a/T005d: Data loading (AdvBench, HF4, Taxonomy)
- T008a: Taxonomy centroid generation
- T013a/T013b/T014: Drift scoring logic
- T017: Export results logic
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import set_seed, ensure_directories, get_path, get_config, get_centroid_model
from data_loader import validate_data_integrity, fetch_advbench, fetch_hf4, fetch_taxonomy
from taxonomy_builder import main as build_taxonomy_main
from drift_scoring import main as run_drift_scoring_main
from utils import load_json_file

def main():
    """
    Orchestrates the full pipeline:
    1. Setup seeds and directories
    2. Ensure taxonomy centroids exist (build if missing)
    3. Ensure raw data exists (fetch if missing)
    4. Run drift scoring
    5. Export results
    """
    print("=== llmXive Zero-Shot Drift Detection Pipeline ===")
    
    # Load configuration
    config = get_config()
    set_seed(config.get('random_seed', 42))
    ensure_directories()
    print(f"[INFO] Seed set to {config.get('random_seed')}")
    print(f"[INFO] Directories ensured.")

    # 2. Ensure Data Exists
    # We attempt to fetch data if not present. 
    # Note: In a real CI/CD or production run, data might be pre-loaded.
    # Here we check for the existence of the raw taxonomy file and logs.
    
    taxonomy_path = get_path('raw_taxonomy')
    if not taxonomy_path.exists():
        print(f"[INFO] Taxonomy not found at {taxonomy_path}. Fetching...")
        try:
            fetch_taxonomy()
            print("[INFO] Taxonomy fetched successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to fetch taxonomy: {e}")
            # If taxonomy is missing, we cannot proceed with centroids
            raise e
    else:
        print(f"[INFO] Taxonomy found at {taxonomy_path}.")

    # Check for log data (AdvBench or HF4)
    # We assume T005a/T005c have run or will run. 
    # For the pipeline to work, we need at least one log file.
    log_files = [get_path('advbench'), get_path('hf4'), get_path('test_static_logs')]
    available_logs = [f for f in log_files if f.exists()]
    
    if not available_logs:
        print("[WARNING] No log data files found. Attempting to fetch AdvBench and HF4...")
        try:
            fetch_advbench()
            fetch_hf4()
            available_logs = [f for f in log_files if f.exists()]
        except Exception as e:
            print(f"[ERROR] Failed to fetch log data: {e}")
            raise e
    
    print(f"[INFO] Available log sources: {[f.name for f in available_logs]}")

    # 3. Build Taxonomy Centroids (if not present)
    centroids_path = get_path('centroids')
    if not centroids_path.exists():
        print(f"[INFO] Centroids not found at {centroids_path}. Building...")
        build_taxonomy_main()
        if not centroids_path.exists():
            raise RuntimeError("Taxonomy builder did not produce centroid file.")
        print("[INFO] Centroids built successfully.")
    else:
        print(f"[INFO] Centroids found at {centroids_path}.")

    # 4. Run Drift Scoring
    print("[INFO] Starting Drift Scoring...")
    try:
        run_drift_scoring_main()
        print("[INFO] Drift Scoring completed.")
    except Exception as e:
        print(f"[ERROR] Drift Scoring failed: {e}")
        raise e

    # 5. Export Results
    # The drift_scoring main() function already calls export_results internally 
    # based on the implementation of T017. 
    # We verify the output exists.
    output_path = get_path('drift_scores_csv')
    if output_path.exists():
        print(f"[SUCCESS] Pipeline completed. Results exported to: {output_path}")
        return 0
    else:
        print(f"[ERROR] Pipeline finished but output file {output_path} not found.")
        return 1

if __name__ == "__main__":
    sys.exit(main())