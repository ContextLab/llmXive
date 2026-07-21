import json
import csv
import subprocess
import sys
import os
import time
from pathlib import Path
from utils.logging import get_logger, log_stage_start, log_stage_end

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

def run_baseline_agent(manifest_path: Path, output_path: Path):
    """Orchestrate the external baseline execution."""
    # In a real scenario, this might call a remote API or a separate process
    # Here we simulate calling the local baseline script as a subprocess
    # to ensure the external flow is tested.
    
    script_path = Path(__file__).resolve().parent / "run_baseline.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--manifest", str(manifest_path),
        "--output", str(output_path)
    ]
    
    logger.info(f"Executing baseline agent: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=120 # 2 minutes timeout
        )
        if result.returncode != 0:
            raise RuntimeError(f"Baseline process failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Baseline process timed out")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Baseline process failed: {e.stderr}")

def validate_results(output_path: Path):
    """Validate that the output file exists and contains valid JSON."""
    if not output_path.exists():
        raise FileNotFoundError(f"Baseline output not generated: {output_path}")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Baseline output is empty or invalid format")
    
    # Check for required keys
    required_keys = {'task_id', 'method', 'time_to_pivot', 'success'}
    for item in data:
        if not required_keys.issubset(item.keys()):
            raise ValueError(f"Missing required keys in baseline result: {item}")

def wait_for_baseline_output(output_path: Path, timeout: int = 300, poll_interval: int = 5):
    """Wait for the baseline output file to appear and be valid."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if output_path.exists():
            try:
                validate_results(output_path)
                return True
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Baseline output not yet valid: {e}")
        time.sleep(poll_interval)
    
    raise TimeoutError(f"Baseline output did not appear within {timeout} seconds")

def main():
    """Main entry point for external baseline orchestration."""
    project_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = project_root / "data" / "derived" / "experiment_manifest.csv"
    output_path = project_root / "data" / "derived" / "baseline_results.json"
    
    log_stage_start("External Baseline Orchestration", "T021b")
    
    try:
        # 1. Run the baseline agent
        run_baseline_agent(manifest_path, output_path)
        
        # 2. Wait and validate (redundant if run_baseline returns, but good for async flows)
        # Since we ran synchronously above, we just validate here
        validate_results(output_path)
        
        logger.info(f"External baseline execution complete. Output: {output_path}")
        log_stage_end("External Baseline Orchestration", "Success")
        
    except Exception as e:
        logger.error(f"External baseline orchestration failed: {e}")
        log_stage_end("External Baseline Orchestration", f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
