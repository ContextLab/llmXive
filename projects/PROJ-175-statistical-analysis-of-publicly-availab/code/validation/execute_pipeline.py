import os
import sys
import json
import time
import psutil
from pathlib import Path

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download import main as download_main
from data.preprocess import main as preprocess_main
from data.split import create_train_test_split, load_subset_size

def get_memory_usage_gb():
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def save_memory_profile(peak_mb, timestamp):
    """Save memory profile to data/memory_profile.json."""
    profile_path = project_root / "data" / "memory_profile.json"
    profile = {
        "peak_ram_mb": peak_mb,
        "timestamp": timestamp,
        "limit_mb": 6144
    }
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)

def run_pipeline_step(step_name, func, *args, **kwargs):
    """Run a pipeline step and handle errors."""
    print(f"Running {step_name}...")
    try:
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"  {step_name} completed in {elapsed:.2f} seconds.")
        return True, elapsed
    except Exception as e:
        print(f"  ERROR in {step_name}: {str(e)}")
        return False, str(e)

def main():
    """Execute the full data download and preprocessing pipeline."""
    start_time = time.time()
    peak_ram_mb = 0.0
    artifacts_created = []
    status = "SUCCESS"
    error_message = None

    # Initialize tracking
    memory_start = get_memory_usage_gb() * 1024
    
    try:
        # Step 1: Data Download (T051, T013)
        success, result = run_pipeline_step("Data Download", download_main)
        if not success:
            raise RuntimeError(f"Data download failed: {result}")
        
        # Check memory after download
        current_ram = get_memory_usage_gb() * 1024
        if current_ram > peak_ram_mb:
            peak_ram_mb = current_ram

        # Step 2: Data Preprocessing (T014, T015, T016, T017, T017b, T018)
        success, result = run_pipeline_step("Data Preprocessing", preprocess_main)
        if not success:
            raise RuntimeError(f"Data preprocessing failed: {result}")

        # Check memory after preprocessing
        current_ram = get_memory_usage_gb() * 1024
        if current_ram > peak_ram_mb:
            peak_ram_mb = current_ram

        # Step 3: Data Split (T019)
        # Note: load_subset_size is called internally by create_train_test_split
        # We just need to ensure the split happens
        success, result = run_pipeline_step("Data Split", create_train_test_split)
        if not success:
            raise RuntimeError(f"Data split failed: {result}")

        # Check memory after split
        current_ram = get_memory_usage_gb() * 1024
        if current_ram > peak_ram_mb:
            peak_ram_mb = current_ram

        # Define expected artifacts based on task dependencies
        expected_artifacts = [
            "data/raw/recipe1m_stream_log.json",
            "data/processed/co_occurrence_matrix.parquet",
            "data/processed/flavor_similarity.parquet",
            "data/processed/ingredient_roles_binned.parquet",
            "data/processed/final_features.parquet",
            "data/split_config.json"
        ]

        # Verify artifacts exist
        for artifact in expected_artifacts:
            artifact_path = project_root / artifact
            if artifact_path.exists():
                artifacts_created.append(artifact)
            else:
                print(f"WARNING: Expected artifact not found: {artifact}")

        end_time = time.time()
        runtime_seconds = end_time - start_time

        # Final memory check
        current_ram = get_memory_usage_gb() * 1024
        if current_ram > peak_ram_mb:
            peak_ram_mb = current_ram

        # Save memory profile
        save_memory_profile(peak_ram_mb, time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        end_time = time.time()
        runtime_seconds = end_time - start_time

    # Prepare execution log
    execution_log = {
        "status": status,
        "runtime_seconds": round(runtime_seconds, 2),
        "peak_ram_mb": round(peak_ram_mb, 2),
        "artifacts_created": artifacts_created
    }

    if error_message:
        execution_log["error"] = error_message

    # Save execution log
    log_path = project_root / "data" / "pipeline_execution_log.json"
    with open(log_path, 'w') as f:
        json.dump(execution_log, f, indent=2)

    print(f"\nPipeline execution log saved to {log_path}")
    print(f"Status: {status}")
    print(f"Runtime: {runtime_seconds:.2f} seconds")
    print(f"Peak RAM: {peak_ram_mb:.2f} MB")
    print(f"Artifacts created: {len(artifacts_created)}")

    return 0 if status == "SUCCESS" else 1

if __name__ == "__main__":
    sys.exit(main())
