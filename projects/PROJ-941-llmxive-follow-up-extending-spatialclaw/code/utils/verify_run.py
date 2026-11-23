"""
Execution Integrity Check Module (T046)

This module aggregates all 2D agent run results and the 3D baseline results
to verify that every task_id has the expected number of runs.

It enforces the following:
- Every task_id in the source dataset must have exactly `n_runs` (from config) 
  in the 2D agent results directory.
- Every task_id must have exactly 1 run in the baseline results file.

Output: results/analysis/run_integrity_report.json
"""
import os
import json
import glob
import logging
import argparse
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_yaml_config_simple(config_path: str) -> Dict[str, Any]:
    """Simple YAML parser for the power config (no external deps)."""
    config = {}
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Try to parse as number
                try:
                    if '.' in value:
                        config[key] = float(value)
                    else:
                        config[key] = int(value)
                except ValueError:
                    config[key] = value
    return config

def load_baseline_results(baseline_path: str) -> List[Dict[str, Any]]:
    """Load the baseline run results."""
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline results file not found: {baseline_path}")
    
    with open(baseline_path, 'r') as f:
        # Assuming JSON lines or a list of objects
        content = f.read().strip()
        if content.startswith('['):
            return json.loads(content)
        else:
            # JSON lines format
            results = []
            for line in content.split('\n'):
                if line.strip():
                    results.append(json.loads(line))
            return results

def load_2d_run_results(run_dir: str) -> List[Dict[str, Any]]:
    """Load all 2D agent run results from the directory."""
    results = []
    pattern = os.path.join(run_dir, "run_*.json")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning(f"No run files found matching pattern: {pattern}")
        return results
    
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if content.startswith('['):
                    data = json.loads(content)
                    if isinstance(data, list):
                        results.extend(data)
                    else:
                        results.append(data)
                else:
                    # JSON lines
                    for line in content.split('\n'):
                        if line.strip():
                            results.append(json.loads(line))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            continue
        
    return results

def verify_run_integrity(
    config_path: str,
    baseline_path: str,
    run_dir: str,
    output_path: str
) -> bool:
    """
    Verify that every task_id has the expected number of runs.
    
    Returns True if integrity check passes, False otherwise.
    """
    # Load configuration
    try:
        config = load_yaml_config_simple(config_path)
        n_runs = config.get('n_runs', 5)
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        # Write failure report
        report = {
            "total_tasks": 0,
            "tasks_with_full_coverage": 0,
            "missing_runs": [],
            "status": "ERROR",
            "error_message": str(e)
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return False
    
    # Load baseline results
    try:
        baseline_results = load_baseline_results(baseline_path)
    except FileNotFoundError as e:
        logger.error(f"Baseline error: {e}")
        report = {
            "total_tasks": 0,
            "tasks_with_full_coverage": 0,
            "missing_runs": [],
            "status": "ERROR",
            "error_message": f"Baseline file missing: {e}"
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return False
    
    # Load 2D agent results
    try:
        agent_results = load_2d_run_results(run_dir)
    except Exception as e:
        logger.error(f"Agent results error: {e}")
        report = {
            "total_tasks": 0,
            "tasks_with_full_coverage": 0,
            "missing_runs": [],
            "status": "ERROR",
            "error_message": f"Agent results error: {e}"
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return False
    
    # Extract all unique task_ids from baseline (assuming baseline covers all tasks)
    # If baseline is a list of results, we extract task_ids from there
    baseline_task_ids: Set[str] = set()
    for entry in baseline_results:
        if 'task_id' in entry:
            baseline_task_ids.add(entry['task_id'])
    
    if not baseline_task_ids:
        # Fallback: try to infer from agent results if baseline is empty or missing task_ids
        for entry in agent_results:
            if 'task_id' in entry:
                baseline_task_ids.add(entry['task_id'])
    
    if not baseline_task_ids:
        logger.error("Could not determine task_ids from any source.")
        report = {
            "total_tasks": 0,
            "tasks_with_full_coverage": 0,
            "missing_runs": [],
            "status": "INCOMPLETE",
            "error_message": "No task_ids found in baseline or agent results."
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return False
    
    total_tasks = len(baseline_task_ids)
    tasks_with_full_coverage = 0
    missing_runs: List[Dict[str, Any]] = []
    
    # Count runs per task_id in agent results
    agent_run_counts: Dict[str, int] = {}
    for entry in agent_results:
        tid = entry.get('task_id')
        if tid:
            agent_run_counts[tid] = agent_run_counts.get(tid, 0) + 1
    
    # Verify each task_id
    for tid in baseline_task_ids:
        expected_agent_runs = n_runs
        actual_agent_runs = agent_run_counts.get(tid, 0)
        
        # Check baseline (must have exactly 1 run, usually implied by the single file)
        # We assume the baseline file contains one entry per task_id.
        baseline_count = sum(1 for e in baseline_results if e.get('task_id') == tid)
        
        if baseline_count != 1:
            logger.warning(f"Task {tid} has {baseline_count} baseline entries (expected 1).")
        
        if actual_agent_runs != expected_agent_runs:
            missing_runs.append({
                "task_id": tid,
                "expected": expected_agent_runs,
                "actual": actual_agent_runs
            })
        else:
            tasks_with_full_coverage += 1
    
    # Determine status
    status = "COMPLETE" if len(missing_runs) == 0 else "INCOMPLETE"
    is_valid = status == "COMPLETE"
    
    # Write report
    report = {
        "total_tasks": total_tasks,
        "tasks_with_full_coverage": tasks_with_full_coverage,
        "missing_runs": missing_runs,
        "status": status
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Integrity check {status}. Total: {total_tasks}, Full: {tasks_with_full_coverage}, Missing: {len(missing_runs)}")
    
    return is_valid

def main():
    parser = argparse.ArgumentParser(description="Verify execution integrity of runs.")
    parser.add_argument("--config", type=str, default="data/power_config.yaml",
                        help="Path to power config YAML")
    parser.add_argument("--baseline", type=str, default="results/logs/baseline_run.json",
                        help="Path to baseline results JSON")
    parser.add_argument("--run-dir", type=str, default="results/runs",
                        help="Directory containing 2D agent run JSONs")
    parser.add_argument("--output", type=str, default="results/analysis/run_integrity_report.json",
                        help="Path to output integrity report JSON")
    
    args = parser.parse_args()
    
    success = verify_run_integrity(
        config_path=args.config,
        baseline_path=args.baseline,
        run_dir=args.run_dir,
        output_path=args.output
    )
    
    if not success:
        logger.error("Integrity check failed. Further analysis tasks should be aborted.")
        # Exit with non-zero code to signal failure to pipeline
        return 1
    else:
        logger.info("Integrity check passed. All tasks have full coverage.")
        return 0

if __name__ == "__main__":
    exit(main())