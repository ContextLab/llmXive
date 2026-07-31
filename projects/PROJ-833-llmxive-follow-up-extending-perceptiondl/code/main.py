import logging
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_data_path, ensure_directories
from models.sequential_runner import run_sequential_pipeline, InferenceResult
from contracts.validator import validate_regression_result, load_schema

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'state' / 'pipeline.log')
    ]
)
logger = logging.getLogger("main")

def log_generation_progress(step: str, current: int, total: int):
    logger.info(f"Progress [{step}]: {current}/{total}")

def log_failure(step: str, reason: str):
    logger.error(f"Failure in {step}: {reason}")

def log_success(step: str, details: Optional[str] = None):
    msg = f"Success in {step}"
    if details:
        msg += f": {details}"
    logger.info(msg)

def load_synthetic_samples(region_counts: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """
    Load synthetic image paths and annotations from data/synthetic/.
    Filters by region_counts if provided.
    """
    data_path = get_data_path()
    synthetic_dir = data_path / "synthetic"
    
    if not synthetic_dir.exists():
        raise FileNotFoundError(f"Synthetic data directory not found: {synthetic_dir}")

    samples = []
    json_files = list(synthetic_dir.glob("*.json"))
    
    logger.info(f"Found {len(json_files)} annotation files in {synthetic_dir}")

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract region count from filename or metadata if available
            # Assuming filename format: image_{region_count}_... or metadata has 'region_count'
            region_count = data.get('region_count')
            if region_count is None:
                # Fallback to parsing filename if metadata missing
                name_parts = json_file.stem.split('_')
                for part in name_parts:
                    if part.isdigit():
                        region_count = int(part)
                        break
            
            if region_count is None:
                logger.warning(f"Could not determine region count for {json_file}, skipping.")
                continue

            if region_counts is None or region_count in region_counts:
                samples.append({
                    "image_path": str(json_file.parent / data.get('image_path', '')),
                    "annotations": data,
                    "region_count": region_count,
                    "json_path": str(json_file)
                })
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")
            continue

    logger.info(f"Loaded {len(samples)} valid synthetic samples.")
    return samples

def run_parallel_inference_pipeline(samples: List[Dict[str, Any]], output_path: Path):
    """
    Placeholder for T019 implementation.
    In a real run, this would call models.parallel_runner.run_parallel_inference.
    """
    logger.info("Parallel inference pipeline skipped for this task (T020 only).")
    # In full implementation:
    # from models.parallel_runner import run_parallel_inference
    # results = run_parallel_inference(samples, output_path)
    # return results

def run_sequential_inference_pipeline(samples: List[Dict[str, Any]], output_path: Path):
    """
    T020 Implementation:
    Run sequential inference via models.sequential_runner (PerceptionDLM with context-reset).
    Save results to data/processed/sequential_results.json.
    Schema: {captions, region_count, inference_time, region_ids}
    """
    logger.info(f"Starting sequential inference pipeline for {len(samples)} samples.")
    logger.info(f"Output destination: {output_path}")
    
    ensure_directories()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_results = []
    successful_count = 0
    failed_count = 0

    # Validate output schema structure against contract if available
    schema_path = PROJECT_ROOT / "contracts" / "regression_result.schema.yaml"
    # Note: The runner output is a list of inference results, which will be aggregated later.
    # We validate individual result structures here if the contract expects a list.
    
    for i, sample in enumerate(samples):
        log_generation_progress("Sequential Inference", i + 1, len(samples))
        
        try:
            # Extract bounding boxes and image path for the runner
            annotations = sample['annotations']
            bounding_boxes = annotations.get('bounding_boxes', [])
            image_path = sample['image_path']
            region_count = sample['region_count']
            
            if not bounding_boxes:
                logger.warning(f"No bounding boxes in {sample['json_path']}, skipping.")
                failed_count += 1
                continue

            # Call the sequential runner
            # The runner expects a list of boxes and an image path
            # It returns a list of InferenceResult objects
            runner_results = run_sequential_pipeline(
                image_path=image_path,
                bounding_boxes=bounding_boxes,
                region_count=region_count
            )

            # Process results into the required schema
            # Schema: {captions, region_count, inference_time, region_ids}
            # We aggregate per-image or per-region depending on runner output structure.
            # Assuming runner returns a list of results for each region.
            
            image_result = {
                "region_count": region_count,
                "captions": [],
                "inference_time": 0.0,
                "region_ids": []
            }
            
            total_time = 0.0
            
            for res in runner_results:
                if isinstance(res, InferenceResult):
                    image_result["captions"].append(res.caption)
                    image_result["region_ids"].append(res.region_id)
                    total_time += res.inference_time
                elif isinstance(res, dict):
                    image_result["captions"].append(res.get("caption", ""))
                    image_result["region_ids"].append(res.get("region_id", -1))
                    total_time += res.get("inference_time", 0.0)
                else:
                    logger.warning(f"Unexpected result type: {type(res)}")

            image_result["inference_time"] = total_time
            all_results.append(image_result)
            successful_count += 1

        except Exception as e:
            logger.error(f"Sequential inference failed for sample {i} ({sample['json_path']}): {e}", exc_info=True)
            failed_count += 1
            continue

    # Write results to disk
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Sequential inference complete. Success: {successful_count}, Failed: {failed_count}")
    logger.info(f"Results saved to {output_path}")
    
    return all_results

def run_pipeline_with_logging(region_counts: Optional[List[int]] = None):
    """
    Main orchestration logic for T020.
    Loads data, runs sequential inference, saves results.
    """
    ensure_directories()
    
    # 1. Load Synthetic Data
    logger.info("Loading synthetic samples...")
    samples = load_synthetic_samples(region_counts)
    
    if not samples:
        logger.error("No synthetic samples found. Cannot proceed.")
        return

    # 2. Run Sequential Inference (T020)
    output_path = get_data_path() / "processed" / "sequential_results.json"
    logger.info(f"Running sequential inference pipeline...")
    
    results = run_sequential_inference_pipeline(samples, output_path)
    
    if not results:
        logger.error("Sequential inference produced no results.")
        return

    log_success("Sequential Inference Pipeline", f"Generated {len(results)} results")

def main():
    """
    Entry point for T020 execution.
    """
    # Default region counts from config (25, 30, 35, 40, 45, 50)
    # In a full run, these would be read from config.py
    region_counts = [25, 30, 35, 40, 45, 50]
    
    try:
        run_pipeline_with_logging(region_counts)
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()