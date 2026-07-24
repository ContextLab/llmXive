import json
import csv
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import set_seed

logger = get_logger(__name__)

def load_annotated_failures(failures_path: Path) -> List[Dict[str, Any]]:
    """Load the annotated failure cases from the JSON file."""
    if not failures_path.exists():
        raise FileNotFoundError(f"Failure cases not found: {failures_path}")
    
    with open(failures_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Failure cases file must contain a JSON array.")
    
    return data

def stratified_sample(failures: List[Dict[str, Any]], n: int, seed: int) -> List[Dict[str, Any]]:
    """
    Select a stratified random sample of failures based on 'annotated_structural_feature'.
    Ensures representation from every stratum. Fails if any stratum has fewer items
    than the calculated minimum share required to reach n total.
    """
    set_seed(seed)
    
    # Group by failure type
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for f in failures:
        ftype = f.get("annotated_structural_feature", "Unstructured")
        if ftype not in groups:
            groups[ftype] = []
        groups[ftype].append(f)
    
    num_groups = len(groups)
    if num_groups == 0:
        raise ValueError("No failure cases found to sample from.")
    
    # Calculate base count per group and remainder
    base_count = n // num_groups
    remainder = n % num_groups
    
    sample: List[Dict[str, Any]] = []
    sorted_types = sorted(groups.keys())
    
    for i, ftype in enumerate(sorted_types):
        # Distribute remainder to the first 'remainder' groups
        count = base_count + (1 if i < remainder else 0)
        
        group_data = groups[ftype]
        if len(group_data) < count:
            raise ValueError(
                f"Stratum '{ftype}' has only {len(group_data)} items, "
                f"but {count} are required to meet the stratified sample size of {n}."
            )
        
        group_samples = random.sample(group_data, count)
        sample.extend(group_samples)
    
    # Sanity check
    if len(sample) != n:
        raise ValueError(f"Sample size mismatch: expected {n}, got {len(sample)}")
    
    return sample

def write_manifest(sample: List[Dict[str, Any]], output_path: Path):
    """Write the manifest to a CSV file with columns: task_id, failure_type."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'failure_type'])
        
        for item in sample:
            task_id = item.get('task_id')
            failure_type = item.get('annotated_structural_feature', 'Unstructured')
            if not task_id:
                raise ValueError("Sample item missing 'task_id' field.")
            writer.writerow([task_id, failure_type])
    
    logger.info(f"Manifest written to {output_path} with {len(sample)} rows.")

def main():
    """Main entry point for manifest generation."""
    project_root = Path(__file__).resolve().parent.parent.parent
    failures_path = project_root / "data" / "derived" / "failure_cases.json"
    output_path = project_root / "data" / "derived" / "experiment_manifest.csv"
    
    log_stage_start("Generate Manifest", "T019a")
    
    try:
        logger.info(f"Loading annotated failures from {failures_path}")
        failures = load_annotated_failures(failures_path)
        logger.info(f"Loaded {len(failures)} failure cases.")
        
        logger.info("Performing stratified random sample (n=100, seed=42)...")
        sample = stratified_sample(failures, n=100, seed=42)
        
        logger.info("Writing manifest to CSV...")
        write_manifest(sample, output_path)
        
        log_stage_end("Generate Manifest", "Success")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        log_stage_end("Generate Manifest", f"Failed: Missing input data - {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Sampling validation failed: {e}")
        log_stage_end("Generate Manifest", f"Failed: Stratification error - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Manifest generation failed unexpectedly: {e}")
        log_stage_end("Generate Manifest", f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()