import json
import csv
import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional
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

def run_baseline_agent(manifest_path: Path, output_path: Path, metrics_path: Path):
    """
    Orchestrate the external baseline execution.
    
    Logic:
    1. Invoke instrument_baseline.py (T021c) as a wrapper to ensure resource metrics are generated.
    2. The script is run synchronously here to ensure the output files exist before returning.
    3. If the process fails, we raise an exception to stop the pipeline.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    instrument_script = project_root / "code" / "03_execution" / "instrument_baseline.py"
    
    if not instrument_script.exists():
        raise FileNotFoundError(f"Instrument baseline script not found: {instrument_script}")
    
    cmd = [
        sys.executable,
        str(instrument_script),
        "--manifest", str(manifest_path),
        "--output", str(output_path),
        "--metrics", str(metrics_path)
    ]
    
    logger.info(f"Executing baseline agent wrapper: {' '.join(cmd)}")
    
    try:
        # Run the baseline agent. 
        # We do NOT enforce an arbitrary timeout that blocks data collection.
        # We let the process run until it completes or fails permanently.
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Baseline process stderr: {result.stderr}")
            raise RuntimeError(f"Baseline process failed with code {result.returncode}: {result.stderr}")
            
        logger.info(f"Baseline process completed successfully.")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Baseline process failed: {e.stderr}")
        raise RuntimeError(f"Baseline process failed: {e.stderr}")

def validate_results(output_path: Path, manifest_tasks: List[Dict[str, Any]]) -> bool:
    """
    Validate that the output file exists and contains valid JSON.
    Checks that all task IDs from the manifest are present in the results.
    """
    if not output_path.exists():
        raise FileNotFoundError(f"Baseline output not generated: {output_path}")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Baseline output is empty or invalid format")
    
    # Check for required keys
    required_keys = {'task_id', 'method', 'time_to_pivot', 'success'}
    result_ids = set()
    
    for item in data:
        if not required_keys.issubset(item.keys()):
            raise ValueError(f"Missing required keys in baseline result: {item}")
        result_ids.add(item['task_id'])
    
    # Verify all manifest tasks are present
    manifest_ids = {t['task_id'] for t in manifest_tasks}
    missing_ids = manifest_ids - result_ids
    
    if missing_ids:
        raise ValueError(f"Baseline results missing task IDs: {missing_ids}")
        
    logger.info(f"Validation passed: all {len(result_ids)} tasks present.")
    return True

def wait_for_baseline_output(output_path: Path, manifest_tasks: List[Dict[str, Any]], poll_interval: int = 5):
    """
    Wait for the baseline output file to appear and be valid.
    Uses a polling loop with exponential backoff logic (simple fixed interval here for robustness).
    Does NOT enforce an arbitrary timeout; waits for completion or permanent failure.
    """
    start_time = time.time()
    last_log = start_time
    
    while True:
        if output_path.exists():
            try:
                validate_results(output_path, manifest_tasks)
                logger.info("Baseline output validated successfully.")
                return
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Baseline output not yet valid: {e}")
        else:
            logger.info("Waiting for baseline output file...")
        
        # Log progress periodically to avoid spamming logs
        current_time = time.time()
        if current_time - last_log > 60:
            logger.info(f"Still waiting for baseline output... ({int(current_time - start_time)}s elapsed)")
            last_log = current_time
        
        time.sleep(poll_interval)

def handle_signal(signum, frame):
    """Handle SIGINT for explicit cancellation."""
    logger.warning("Received SIGINT. Cancelling baseline orchestration...")
    sys.exit(1)

def main():
    """Main entry point for external baseline orchestration."""
    # Set up signal handler for explicit cancellation
    signal.signal(signal.SIGINT, handle_signal)
    
    project_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = project_root / "data" / "derived" / "experiment_manifest.csv"
    output_path = project_root / "data" / "derived" / "baseline_results.json"
    metrics_path = project_root / "data" / "derived" / "baseline_resource_metrics.json"
    
    log_stage_start("External Baseline Orchestration", "T021")
    
    try:
        # 1. Load manifest to know what we expect
        manifest_tasks = load_manifest(manifest_path)
        logger.info(f"Loaded manifest with {len(manifest_tasks)} tasks.")
        
        # 2. Run the baseline agent (invokes T021c)
        # This will block until the baseline process completes or fails.
        run_baseline_agent(manifest_path, output_path, metrics_path)
        
        # 3. Wait and validate (redundant if run_baseline returns successfully, 
        #    but ensures file integrity and completeness before proceeding)
        # Since run_baseline_agent waits for the subprocess to finish, the file should exist.
        # We validate strictly that all manifest IDs are present.
        validate_results(output_path, manifest_tasks)
        
        # 4. Validate metrics file exists as well (generated by T021c)
        if not metrics_path.exists():
            logger.warning(f"Metrics file not found: {metrics_path}. This may be acceptable if T021c did not generate it, but expected.")
        else:
            logger.info(f"Metrics file found: {metrics_path}")
        
        logger.info(f"External baseline execution complete. Output: {output_path}")
        log_stage_end("External Baseline Orchestration", "Success")
        
    except Exception as e:
        logger.error(f"External baseline orchestration failed: {e}")
        log_stage_end("External Baseline Orchestration", f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()