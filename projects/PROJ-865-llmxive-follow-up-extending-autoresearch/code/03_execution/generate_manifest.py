import json
import csv
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import set_seed

logger = get_logger(__name__)

def load_annotated_failures(failures_path: Path) -> List[Dict[str, Any]]:
    """Load the annotated failure cases from the derived data directory."""
    if not failures_path.exists():
        raise FileNotFoundError(f"Failure cases not found: {failures_path}")
    
    with open(failures_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of failure cases in {failures_path}, got {type(data)}")
    
    return data

def validate_stratification(failures: List[Dict[str, Any]], target_n: int) -> Tuple[bool, str]:
    """
    Validate that we can construct a stratified sample of size target_n.
    Returns (True, '') if possible, (False, error_message) otherwise.
    """
    groups = {}
    for f in failures:
        ftype = f.get("annotated_structural_feature", "Unstructured")
        if ftype not in groups:
            groups[ftype] = []
        groups[ftype].append(f)
    
    if len(groups) == 0:
        return False, "No failure cases found to stratify."
    
    total_available = len(failures)
    if total_available < target_n:
        return False, f"Insufficient data: requested {target_n} samples but only {total_available} available."
    
    per_group = target_n // len(groups)
    remainder = target_n % len(groups)
    
    # Check if each group has enough items
    sorted_types = sorted(groups.keys())
    for i, ftype in enumerate(sorted_types):
        count_needed = per_group + (1 if i < remainder else 0)
        if len(groups[ftype]) < count_needed:
            return False, f"Stratum '{ftype}' has only {len(groups[ftype])} items, need {count_needed}."
    
    return True, "Stratification feasible."

def stratified_sample(failures: List[Dict[str, Any]], n: int, seed: int) -> List[Dict[str, Any]]:
    """
    Select a stratified random sample of size n based on 'annotated_structural_feature'.
    Uses the fixed seed for reproducibility.
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
    
    # Distribute remainder deterministically across sorted groups
    sorted_types = sorted(groups.keys())
    
    for i, ftype in enumerate(sorted_types):
        count = per_group + (1 if i < remainder else 0)
        # Shuffle the group internally to ensure random selection within the stratum
        current_group = groups[ftype]
        random.shuffle(current_group)
        group_samples = current_group[:count]
        sample.extend(group_samples)
    
    # Sanity check
    if len(sample) != n:
        raise ValueError(f"Sample size mismatch: expected {n}, got {len(sample)}")
    
    return sample

def write_manifest(sample: List[Dict[str, Any]], output_path: Path):
    """
    Write the manifest to a CSV file.
    Columns: task_id, failure_type
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'failure_type'])
        
        for item in sample:
            task_id = item.get('task_id', 'UNKNOWN')
            failure_type = item.get('annotated_structural_feature', 'Unstructured')
            writer.writerow([task_id, failure_type])
    
    logger.info(f"Manifest written to {output_path} with {len(sample)} rows.")

def main():
    """Main entry point for manifest generation."""
    project_root = Path(__file__).resolve().parent.parent.parent
    failures_path = project_root / "data" / "derived" / "failure_cases.json"
    output_path = project_root / "data" / "derived" / "experiment_manifest.csv"
    
    log_stage_start("Generate Manifest", "T019a")
    
    try:
        # 1. Load data
        logger.info(f"Loading annotated failures from {failures_path}")
        failures = load_annotated_failures(failures_path)
        logger.info(f"Loaded {len(failures)} failure cases.")
        
        # 2. Validate feasibility
        target_n = 100
        feasible, msg = validate_stratification(failures, target_n)
        if not feasible:
            raise ValueError(f"Stratification check failed: {msg}")
        
        # 3. Perform stratified sampling
        logger.info(f"Performing stratified sample of size {target_n} with seed 42")
        sample = stratified_sample(failures, target_n, seed=42)
        
        # 4. Verify sample size
        if len(sample) != target_n:
            raise ValueError(f"Sample size mismatch: expected {target_n}, got {len(sample)}")
        
        # 5. Write output
        write_manifest(sample, output_path)
        
        log_stage_end("Generate Manifest", "Success")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        log_stage_end("Generate Manifest", f"Failed: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        log_stage_end("Generate Manifest", f"Failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Manifest generation failed unexpectedly: {e}")
        log_stage_end("Generate Manifest", f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()