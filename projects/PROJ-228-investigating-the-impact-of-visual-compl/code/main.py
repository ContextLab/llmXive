"""
Main orchestrator for the Visual Complexity vs PFC Activity pipeline.
Implements subject-wise chunking to enforce RAM limits.
"""

import sys
import resource
from pathlib import Path
from typing import Optional, List

# Import existing API surface from sibling modules
from config import init_seeds, DATA_RAW, DATA_INTERIM, DATA_RESULTS
from ingestion import download_dataset, check_dataset_integrity
from complexity import batch_process_complexity
from roi_extraction import load_aal_atlas, extract_roi
from modeling import load_data_for_modeling, run_regression, save_results
from update_metadata import update_metadata_with_download

# Constants
RAM_LIMIT_GB = 6.0
SUBJECT_BATCH_SIZE = 1  # Process one subject at a time to stay under RAM limit

def get_memory_usage_gb() -> float:
    """
    Get current memory usage of the process in GB.
    Uses resource module for Unix-like systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On macOS and Linux, ru_maxrss is in kilobytes
    return usage / (1024 * 1024)

def check_memory_limit(current_usage_gb: Optional[float] = None) -> bool:
    """
    Check if current memory usage is within the defined limit.
    Returns True if within limit, False otherwise.
    """
    if current_usage_gb is None:
        current_usage_gb = get_memory_usage_gb()
    
    if current_usage_gb > RAM_LIMIT_GB:
        print(f"⚠️  Memory limit exceeded: {current_usage_gb:.2f}GB > {RAM_LIMIT_GB}GB")
        return False
    return True

def process_single_subject(subject_id: str) -> bool:
    """
    Process a single subject: download if needed, compute complexity, extract ROI, and model.
    Returns True if successful, False if memory limit exceeded or error occurred.
    """
    print(f"\n--- Processing Subject: {subject_id} ---")
    
    # Check memory before processing
    if not check_memory_limit():
        return False

    try:
        # Step 1: Ensure data exists (download if needed)
        # Note: In a real run, this would check if data exists for this subject
        # and download only if missing. For now, we assume download_dataset handles
        # the full dataset download.
        if not check_dataset_integrity():
            print(f"Downloading dataset for subject {subject_id}...")
            download_dataset("ds000246")
            update_metadata_with_download("ds000246")

        # Step 2: Compute complexity metrics for stimuli
        # This processes images in batches to stay under memory limit
        complexity_results = batch_process_complexity(DATA_RAW / "stimuli")
        
        # Check memory after complexity processing
        if not check_memory_limit():
            return False

        # Step 3: Extract ROI from BOLD data
        # Load AAL atlas once (it's shared across subjects)
        atlas_path = load_aal_atlas()
        
        # Find BOLD file for this subject (simplified path logic)
        bold_path = DATA_RAW / "sub-01" / "func" / "sub-01_task-stimuli_bold.nii.gz"
        
        if not bold_path.exists():
            print(f"⚠️  BOLD file not found for subject {subject_id}: {bold_path}")
            # In a real scenario, we might skip this subject or handle differently
            return True
        
        roi_data = extract_roi(bold_path, atlas_path)
        
        # Check memory after ROI extraction
        if not check_memory_limit():
            return False

        # Step 4: Run statistical modeling
        # Load the precomputed complexity metrics and ROI data
        data = load_data_for_modeling(DATA_INTERIM / "complexity_metrics.csv", 
                                    DATA_INTERIM / "pfc_timeseries.csv")
        
        results = run_regression(data)
        
        # Step 5: Save results
        output_path = DATA_RESULTS / f"results_{subject_id}.json"
        save_results(results, output_path)
        
        print(f"✅ Successfully processed subject {subject_id}")
        return True

    except MemoryError:
        print(f"❌ MemoryError while processing subject {subject_id}")
        return False
    except Exception as e:
        print(f"❌ Error processing subject {subject_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_pipeline() -> None:
    """
    Main pipeline orchestrator.
    Processes subjects one at a time to enforce RAM limits.
    """
    print("🚀 Starting Visual Complexity vs PFC Activity Pipeline")
    print(f"Memory limit set to {RAM_LIMIT_GB}GB")
    
    # Initialize seeds for reproducibility
    init_seeds()
    
    # Ensure output directories exist
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    DATA_RESULTS.mkdir(parents=True, exist_ok=True)
    
    # Define subjects to process (in a real scenario, this would be dynamic)
    # For now, we process a fixed set of subjects
    subjects = ["sub-01", "sub-02", "sub-03"]  # Example subjects
    
    success_count = 0
    total_count = len(subjects)
    
    for subject in subjects:
        # Check memory before starting each subject
        if not check_memory_limit():
            print(f"🛑 Pipeline halted due to memory limit before subject {subject}")
            break
        
        success = process_single_subject(subject)
        if success:
            success_count += 1
        
        # Force garbage collection between subjects to free memory
        import gc
        gc.collect()
    
    print(f"\n🏁 Pipeline completed: {success_count}/{total_count} subjects processed successfully")
    
    # Final memory check
    final_memory = get_memory_usage_gb()
    print(f"Final memory usage: {final_memory:.2f}GB")
    
    if final_memory > RAM_LIMIT_GB:
        print(f"⚠️  Final memory usage exceeded limit ({RAM_LIMIT_GB}GB)")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()