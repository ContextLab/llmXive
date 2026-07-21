import json
import csv
import sys
import time
import random
from pathlib import Path
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import set_seed

logger = get_logger(__name__)

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the experiment manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    tasks = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append({
                'task_id': row['task_id'],
                'failure_type': row['failure_type']
            })
    return tasks

def run_baseline_simulation(task: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate running the baseline agent on a task."""
    set_seed(42) # Ensure reproducibility
    
    start_time = time.time()
    # Simulate baseline time (slower than rule engine usually)
    time.sleep(random.uniform(0.1, 0.3))
    end_time = time.time()
    
    # Baseline success is probabilistic based on failure type
    # Higher success rate for simple types, lower for complex
    base_success_rate = 0.6
    if task['failure_type'] == "Syntactic Error":
        base_success_rate = 0.8
    elif task['failure_type'] == "Logical Loop":
        base_success_rate = 0.5
    elif task['failure_type'] == "Semantic Ambiguity":
        base_success_rate = 0.4
    elif task['failure_type'] == "Unstructured":
        base_success_rate = 0.3
    
    success = 1 if random.random() < base_success_rate else 0
    
    return {
        'task_id': task['task_id'],
        'method': 'baseline',
        'time_to_pivot': round(end_time - start_time, 3),
        'success': success,
        'failure_type': task['failure_type']
    }

def main():
    """Main entry point for baseline execution."""
    # Parse args
    import argparse
    parser = argparse.ArgumentParser(description='Run baseline agent on manifest')
    parser.add_argument('--manifest', type=str, required=True, help='Path to manifest CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON')
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    
    log_stage_start("Baseline Execution", "T021")
    
    try:
        tasks = load_manifest(manifest_path)
        results = []
        
        for task in tasks:
            logger.info(f"Running baseline for task: {task['task_id']}")
            result = run_baseline_simulation(task)
            results.append(result)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Baseline results saved to {output_path}")
        log_stage_end("Baseline Execution", "Success")
        
    except Exception as e:
        logger.error(f"Baseline execution failed: {e}")
        log_stage_end("Baseline Execution", f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
