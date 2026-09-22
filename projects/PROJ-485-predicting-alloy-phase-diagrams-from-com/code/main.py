"""
Pipeline Orchestrator for Predicting Alloy Phase Diagrams.

This module manages the execution flow of the research pipeline,
handling state persistence, step execution, and error recovery.
"""
import os
import sys
import argparse
import yaml
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.checksum import compute_file_sha256
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

STATE_DIR = "state/PROJ-485"
STATE_FILE = os.path.join(STATE_DIR, "pipeline_state.yaml")
CONFIG_FILE = "code/config.yaml"

# Define the pipeline steps in execution order
PIPELINE_STEPS = [
    {
        "id": "T009",
        "name": "Configuration Validation",
        "module": "utils.config_validator",
        "func": "main",
        "description": "Validate config.yaml and data source availability"
    },
    {
        "id": "T012_T018",
        "name": "Data Ingestion & Feature Generation",
        "module": "ingest.load_data",
        "func": "main",
        "description": "Load raw data, filter, generate descriptors"
    },
    {
        "id": "T022",
        "name": "LOSO Pre-checks (Convex Hull)",
        "module": "models.loso_checks",
        "func": "main",
        "description": "Validate element scope and generate convex hull"
    },
    {
        "id": "T021_T029",
        "name": "Model Training & Evaluation",
        "module": "models.train",
        "func": "main",
        "description": "Train RF model, run LOSO, power analysis, baseline comparison"
    },
    {
        "id": "T032_T038",
        "name": "Visualization & Fidelity",
        "module": "viz.plot_phase_diagrams",
        "func": "main",
        "description": "Generate plots and fidelity reports"
    }
]

def ensure_state_directory():
    """Ensure the state directory exists."""
    if not os.path.exists(STATE_DIR):
        os.makedirs(STATE_DIR, exist_ok=True)
        logger.info(f"Created state directory: {STATE_DIR}")

def load_state() -> Dict[str, Any]:
    """Load the current pipeline state from disk."""
    ensure_state_directory()
    if not os.path.exists(STATE_FILE):
        state = {
            "project_id": "PROJ-485",
            "start_time": None,
            "end_time": None,
            "status": "initialized",
            "steps": {}
        }
        save_state(state)
        return state

    try:
        with open(STATE_FILE, 'r') as f:
            state = yaml.safe_load(f)
            if not state:
                state = {"project_id": "PROJ-485", "status": "initialized", "steps": {}}
            return state
    except Exception as e:
        log_error(f"Failed to load state file: {e}", ErrorCode.RESOURCE_LIMIT_EXCEEDED)
        return {"project_id": "PROJ-485", "status": "error", "steps": {}}

def save_state(state: Dict[str, Any]):
    """Save the pipeline state to disk."""
    ensure_state_directory()
    try:
        with open(STATE_FILE, 'w') as f:
            yaml.dump(state, f, default_flow_style=False)
        logger.info(f"State saved to {STATE_FILE}")
    except Exception as e:
        log_error(f"Failed to save state file: {e}", ErrorCode.RESOURCE_LIMIT_EXCEEDED)
        raise

def update_step_status(step_id: str, status: str, details: Optional[Dict] = None):
    """Update the status of a specific step in the state."""
    state = load_state()
    if "steps" not in state:
        state["steps"] = {}

    timestamp = datetime.now().isoformat()
    state["steps"][step_id] = {
        "status": status,
        "timestamp": timestamp,
        "details": details or {}
    }

    if status == "running":
        state["status"] = "running"
    elif status == "completed":
        # Check if all steps are completed
        all_completed = all(
            s.get("status") == "completed"
            for s in state["steps"].values()
        )
        if all_completed:
            state["status"] = "completed"
            state["end_time"] = timestamp
    elif status == "failed":
        state["status"] = "failed"
        state["end_time"] = timestamp

    save_state(state)

def run_step(step_config: Dict[str, Any]) -> bool:
    """Execute a single pipeline step."""
    step_id = step_config["id"]
    module_name = step_config["module"]
    func_name = step_config["func"]
    description = step_config["description"]

    log_info(f"Starting step: {step_id} - {description}")
    update_step_status(step_id, "running")

    try:
        # Dynamically import the module
        # Handle relative imports based on project structure
        full_module_path = f"code.{module_name}"
        if module_name.startswith("utils"):
            full_module_path = f"code.{module_name}"
        
        try:
            mod = __import__(full_module_path, fromlist=[func_name])
        except ImportError as e:
            # Fallback for cases where 'code' prefix might be handled differently
            mod = __import__(module_name, fromlist=[func_name])

        func = getattr(mod, func_name)

        # Execute the function
        result = func()

        if result is None or result == 0:
            log_info(f"Step {step_id} completed successfully.")
            update_step_status(step_id, "completed", {"result": "success"})
            return True
        else:
            log_warning(f"Step {step_id} returned non-zero exit code: {result}")
            update_step_status(step_id, "failed", {"result": result})
            return False

    except Exception as e:
        log_error(f"Step {step_id} failed with exception: {e}", ErrorCode.RESOURCE_LIMIT_EXCEEDED)
        update_step_status(step_id, "failed", {"error": str(e)})
        return False

def run_pipeline(args):
    """Run the full pipeline sequentially."""
    state = load_state()
    state["start_time"] = datetime.now().isoformat()
    state["status"] = "running"
    save_state(state)

    log_info("Pipeline execution started.")

    # Filter steps if specific step ID is requested
    steps_to_run = PIPELINE_STEPS
    if args.step:
        steps_to_run = [s for s in PIPELINE_STEPS if s["id"] == args.step]
        if not steps_to_run:
            log_error(f"Step {args.step} not found in pipeline definition.", ErrorCode.RESOURCE_LIMIT_EXCEEDED)
            return 1

    for step in steps_to_run:
        if not run_step(step):
            log_error("Pipeline halted due to step failure.", ErrorCode.RESOURCE_LIMIT_EXCEEDED)
            return 1

    log_info("Pipeline execution completed successfully.")
    return 0

def main():
    """Main entry point for the pipeline orchestrator."""
    parser = argparse.ArgumentParser(description="Alloy Phase Diagram Prediction Pipeline")
    parser.add_argument("--step", type=str, help="Run a specific step ID only")
    parser.add_argument("--reset", action="store_true", help="Reset state file before running")
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            logger.info("State file reset.")

    return run_pipeline(args)

if __name__ == "__main__":
    sys.exit(main())