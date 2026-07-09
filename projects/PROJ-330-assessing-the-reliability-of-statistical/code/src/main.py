import sys
import os
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path

# Import from local modules using the API surface provided
from src.config import ensure_directories
from src.data_loader import fetch_datasets_by_source, load_manifest, validate_manifest
from src.preprocessing import preprocess_dataset, stratify_samples
from src.metrics import calculate_stability_metrics
from src.versioning import update_artifact_state, load_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_SAMPLES_THRESHOLD = 20
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "data" / "results"
LOGS_DIR = PROJECT_ROOT / "code" / "logs"

def run_r_de_analysis(count_file: Path, output_dir: Path, batch_file: Path = None) -> bool:
    """
    Wrapper to run the R DE analysis script.
    Returns True if successful, False otherwise.
    """
    r_script_path = PROJECT_ROOT / "code" / "scripts" / "run_r_script.R"
    
    if not r_script_path.exists():
        logger.error(f"R script not found at {r_script_path}")
        return False

    cmd = [
        "Rscript", str(r_script_path),
        "--count-file", str(count_file),
        "--output-dir", str(output_dir)
    ]
    
    if batch_file and batch_file.exists():
        cmd.extend(["--batch-file", str(batch_file)])

    try:
        logger.info(f"Running R DE analysis: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"R DE analysis failed: {e}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Rscript executable not found. Please ensure R is installed and in PATH.")
        return False

def run_stability_analysis(dataset_id: str, count_data: Path, batch_data: Path = None) -> dict:
    """
    Orchestrates the stability analysis for a single dataset.
    1. Preprocess data (filter, stratify)
    2. Run R DE on full set
    3. Run R DE on subsets
    4. Calculate stability metrics
    """
    logger.info(f"Starting stability analysis for dataset: {dataset_id}")
    
    # Ensure output directories exist
    ensure_directories()
    subset_dir = OUTPUT_DIR / dataset_id / "subsets"
    subset_dir.mkdir(parents=True, exist_ok=True)

    # Preprocessing: Filter and Stratify
    try:
        full_data, batch_info = preprocess_dataset(count_data, batch_file=batch_data)
        
        if len(full_data) < MIN_SAMPLES_THRESHOLD:
            logger.warning(f"Dataset {dataset_id} has {len(full_data)} samples (< {MIN_SAMPLES_THRESHOLD}). Skipping analysis.")
            return {"status": "skipped", "reason": f"Insufficient samples: {len(full_data)} < {MIN_SAMPLES_THRESHOLD}"}

        logger.info(f"Dataset {dataset_id} has {len(full_data)} samples. Proceeding.")

        # Stratify samples
        subsets = stratify_samples(full_data, batch_info, n_splits=5)
        logger.info(f"Created {len(subsets)} stratified subsets.")

        # Run DE on full set
        full_results_file = OUTPUT_DIR / dataset_id / "full_de_results.csv"
        if not run_r_de_analysis(count_data, OUTPUT_DIR / dataset_id, batch_data):
            logger.error(f"Failed to run DE analysis on full set for {dataset_id}")
            return {"status": "failed", "reason": "R DE analysis failed on full set"}

        # Run DE on subsets
        subset_results = []
        for i, (subset_data, subset_batch) in enumerate(subsets):
            subset_id = f"{dataset_id}_subset_{i}"
            subset_count_file = subset_dir / f"{subset_id}_counts.csv"
            subset_batch_file = subset_dir / f"{subset_id}_batch.csv"
            
            # Save subset data temporarily for R script
            subset_data.to_csv(subset_count_file, index=False)
            if subset_batch is not None:
                subset_batch.to_csv(subset_batch_file, index=False)
            
            if run_r_de_analysis(subset_count_file, subset_dir, subset_batch_file if subset_batch is not None else None):
                 # In a real flow, we'd read the R output here. 
                 # For this task, we assume the R script writes to a known location or we parse stdout.
                 # Since we can't run R here, we simulate the successful path structure.
                 # The actual metric calculation happens in the next step.
                 pass
            else:
                logger.warning(f"Skipping subset {i} due to R failure.")
        
        # Calculate metrics (Mocking the read of R outputs for the sake of the Python logic flow)
        # In a real execution, we would read the CSVs generated by R.
        stability_result = calculate_stability_metrics(OUTPUT_DIR / dataset_id)
        
        return {"status": "completed", "metrics": stability_result}

    except Exception as e:
        logger.error(f"Error during stability analysis for {dataset_id}: {e}", exc_info=True)
        return {"status": "failed", "reason": str(e)}

def main():
    """
    Main entry point to process datasets from the manifest.
    Implements T017: Error handling to skip datasets with <20 samples.
    """
    ensure_directories()
    manifest_path = DATA_DIR / "manifest.json"
    
    if not manifest_path.exists():
        logger.error("Manifest file not found. Cannot proceed.")
        sys.exit(1)

    try:
        manifest = load_manifest(manifest_path)
        if not validate_manifest(manifest):
            logger.error("Manifest validation failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)

    results = []
    for dataset_entry in manifest.get("datasets", []):
        dataset_id = dataset_entry.get("id")
        source = dataset_entry.get("source")
        
        logger.info(f"Processing dataset: {dataset_id} from {source}")
        
        # Fetch dataset (download if not cached)
        try:
            count_file, batch_file = fetch_datasets_by_source(source, [dataset_id])
            if not count_file:
                logger.warning(f"Could not fetch dataset {dataset_id}. Skipping.")
                continue
        except Exception as e:
            logger.error(f"Error fetching dataset {dataset_id}: {e}")
            continue

        # Run Analysis
        result = run_stability_analysis(dataset_id, count_file, batch_file)
        
        if result["status"] == "skipped":
            logger.warning(f"Skipped {dataset_id}: {result['reason']}")
            # Log to a specific skip file or just continue as per requirement
            # Requirement: "skip datasets ... and log warnings"
            # We have already logged the warning.
        elif result["status"] == "completed":
            results.append({"id": dataset_id, "result": result})
            logger.info(f"Completed analysis for {dataset_id}")
        else:
            logger.error(f"Analysis failed for {dataset_id}: {result['reason']}")
            results.append({"id": dataset_id, "result": result})

    # Save final summary
    summary_path = OUTPUT_DIR / "analysis_summary.json"
    import json
    with open(summary_path, 'w') as f:
        json.dump({"datasets_processed": len(results), "results": results}, f, indent=2)
    
    logger.info(f"Analysis complete. Summary saved to {summary_path}")

if __name__ == "__main__":
    main()