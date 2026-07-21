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
    """Load the annotated failure cases."""
    if not failures_path.exists():
        raise FileNotFoundError(f"Failure cases not found: {failures_path}")
    
    with open(failures_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def stratified_sample(failures: List[Dict[str, Any]], n: int, seed: int) -> List[Dict[str, Any]]:
    """Select a stratified sample of failures."""
    set_seed(seed)
    
    # Group by failure type
    groups = {}
    for f in failures:
        ftype = f.get("annotated_structural_feature", "Unstructured")
        if ftype not in groups:
            groups[ftype] = []
        groups[ftype].append(f)
    
    sample = []
    total_needed = n
    per_group = total_needed // len(groups)
    remainder = total_needed % len(groups)
    
    # Distribute remainder
    sorted_types = sorted(groups.keys())
    for i, ftype in enumerate(sorted_types):
        count = per_group + (1 if i < remainder else 0)
        group_samples = random.sample(groups[ftype], min(count, len(groups[ftype])))
        sample.extend(group_samples)
    
    return sample

def write_manifest(sample: List[Dict[str, Any]], output_path: Path):
    """Write the manifest to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'failure_type'])
        
        for item in sample:
            writer.writerow([item['task_id'], item['annotated_structural_feature']])
    
    logger.info(f"Manifest written to {output_path}")

def main():
    """Main entry point for manifest generation."""
    project_root = Path(__file__).resolve().parent.parent.parent
    failures_path = project_root / "data" / "derived" / "failure_cases.json"
    output_path = project_root / "data" / "derived" / "experiment_manifest.csv"
    
    log_stage_start("Generate Manifest", "T019a")
    
    try:
        failures = load_annotated_failures(failures_path)
        sample = stratified_sample(failures, 100, 42)
        write_manifest(sample, output_path)
        
        log_stage_end("Generate Manifest", "Success")
        
    except Exception as e:
        logger.error(f"Manifest generation failed: {e}")
        log_stage_end("Generate Manifest", f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
