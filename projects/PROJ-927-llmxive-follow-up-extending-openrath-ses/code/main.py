import argparse
import os
import sys
import time
import signal
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from config import (
    load_state, save_state, ensure_directories,
    SEED, CORRUPTION_RATE, WORKFLOW_COUNT, SWEEP_RATES,
    RAW_DATA_DIR, PROCESSED_DATA_DIR, STATE_DIR
)
from generators.workflow_generator import generate_ground_truth_batch
from simulators.corruption_injector import CorruptionInjector
from simulators.corruption_log_manager import (
    mark_workflow_corrupted, clear_corruption_log, load_corruption_map
)
from executors.event_log_executor import EventLogExecutor
from executors.session_first_executor import SessionFirstExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestration")
    parser.add_argument('--seed', type=int, default=SEED, help='Random seed')
    parser.add_argument('--count', type=int, default=WORKFLOW_COUNT, help='Number of workflows')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--corruption-rate', type=float, default=CORRUPTION_RATE, help='Corruption rate')
    parser.add_argument('--sweep', action='store_true', help='Run sensitivity sweep')
    return parser.parse_args()

def load_checkpoint() -> Dict[str, Any]:
    state_path = Path(STATE_DIR) / "projects" / "PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"
    if not state_path.exists():
        return {"checkpoint": {"last_workflow_id": -1, "status": "pending"}}
    # Simple YAML/JSON load for state
    with open(state_path, 'r') as f:
        # Assuming simple key-value or JSON structure for state
        try:
            import yaml
            content = yaml.safe_load(f)
        except ImportError:
            # Fallback if yaml not available, though requirements.txt has it
            import json
            content = json.load(f)
    return content.get("checkpoint", {"last_workflow_id": -1, "status": "pending"})

def save_checkpoint(last_id: int, status: str):
    state_path = Path(STATE_DIR) / "projects" / "PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"
    ensure_directories()
    content = {
        "checkpoint": {
            "last_workflow_id": last_id,
            "status": status
        }
    }
    # Write as YAML if possible, else JSON
    try:
        import yaml
        with open(state_path, 'w') as f:
            yaml.dump(content, f)
    except ImportError:
        with open(state_path, 'w') as f:
            json.dump(content, f)
    logger.info(f"Saved checkpoint: workflow {last_id}, status {status}")

def get_workflows_to_process(count: int, resume: bool) -> List[int]:
    if not resume:
        return list(range(count))
    checkpoint = load_checkpoint()
    last_id = checkpoint.get("last_workflow_id", -1)
    if last_id >= count - 1:
        return []
    return list(range(last_id + 1, count))

def process_single_workflow(workflow_id: int, corruption_rate: float):
    """
    Process a single workflow:
    1. Generate ground truth (if not exists) - handled by batch generator
    2. Execute via Baseline (Event Log)
    3. Execute via Experimental (Session First)
    4. Inject corruption
    5. MARK corruption in central log (T026)
    """
    logger.info(f"Processing workflow {workflow_id} with corruption rate {corruption_rate}")
    
    # 1. Ensure ground truth exists (Assuming batch generation happened or happens here)
    # In a real pipeline, generation might be a separate step, but for flow:
    # We assume generate_ground_truth_batch is called before or handles missing ones.
    
    # 2. Execute Baseline
    baseline_executor = EventLogExecutor(workflow_id=workflow_id, seed=SEED)
    baseline_result = baseline_executor.execute(corruption_rate=0.0) # No corruption yet, just execution
    
    # 3. Execute Session First
    session_executor = SessionFirstExecutor(workflow_id=workflow_id, seed=SEED)
    session_result = session_executor.execute(corruption_rate=0.0)
    
    # 4. Inject Corruption
    injector = CorruptionInjector(
        workflow_id=workflow_id,
        corruption_rate=corruption_rate,
        base_seed=SEED
    )
    
    corrupted_files = injector.inject()
    
    # 5. MARK CORRUPTION IN CENTRAL LOG (T026 Implementation)
    if corrupted_files:
        # Determine the type of corruption based on what was returned
        # injector.inject() returns a list of modified/deleted files
        # We mark the workflow as corrupted in the central map
        mark_workflow_corrupted(
            workflow_id=str(workflow_id),
            corruption_type="mixed", # Or specific types if injector returns them
            details={
                "modified_files": corrupted_files.get("modified", []),
                "deleted_files": corrupted_files.get("deleted", []),
                "corruption_rate_applied": corruption_rate
            }
        )
        logger.info(f"Workflow {workflow_id} marked as corrupted in central map.")
    else:
        # Even if no files were hit by RNG, we might want to log that it was processed
        # But strictly, if no corruption happened, maybe don't mark?
        # The task says "mark corrupted files". If none corrupted, no entry needed.
        pass

    save_checkpoint(workflow_id, "completed")

def run_sweep():
    """Run the pipeline for all corruption rates in SWEEP_RATES."""
    logger.info(f"Starting sensitivity sweep over rates: {SWEEP_RATES}")
    for rate in SWEEP_RATES:
        logger.info(f"Running sweep for rate {rate}")
        # Clear corruption log for fresh sweep if needed, or append?
        # Spec implies distinct runs or distinct entries. We'll clear for clean sweep per rate.
        clear_corruption_log()
        run_pipeline(count=WORKFLOW_COUNT, corruption_rate=rate, resume=False)
    logger.info("Sweep completed.")

def run_pipeline(count: int, corruption_rate: float, resume: bool = True):
    """Main pipeline execution loop."""
    workflow_ids = get_workflows_to_process(count, resume)
    if not workflow_ids:
        logger.info("No workflows to process.")
        return
    
    for wid in workflow_ids:
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(300) # 5 min timeout per workflow
            process_single_workflow(wid, corruption_rate)
            signal.alarm(0)
        except TimeoutError:
            logger.error(f"Timeout processing workflow {wid}")
            save_checkpoint(wid, "timeout")
            break
        except Exception as e:
            logger.error(f"Error processing workflow {wid}: {e}")
            save_checkpoint(wid, "error")
            break

def main():
    args = parse_args()
    ensure_directories()
    
    # Generate ground truth batch first if not done
    # Assuming T012/T013 handles this, but we ensure it here for flow
    if not os.path.exists(RAW_DATA_DIR) or not any(Path(RAW_DATA_DIR).glob("*")):
        logger.info("Generating ground truth batch...")
        generate_ground_truth_batch(count=WORKFLOW_COUNT, seed=args.seed)
    
    if args.sweep:
        run_sweep()
    else:
        run_pipeline(count=args.count, corruption_rate=args.corruption_rate, resume=args.resume)

if __name__ == "__main__":
    main()
