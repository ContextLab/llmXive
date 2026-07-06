"""
Pipeline Orchestrator for Alloy Phase Diagram Prediction.

This module manages the execution flow of the research pipeline, handling
state persistence, step execution, and error management.

State is managed in `state/PROJ-485/` as per Constitution Principle V.
"""

import os
import sys
import argparse
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add project root to path to resolve relative imports if running as script
# Note: In a packaged environment, these would be installed imports.
# We assume the execution context allows importing from code/ subpackages.
try:
    from utils.logging import get_logger, log_error, log_info, log_warning
    from utils.checksum import compute_file_sha256, compute_and_store_checksum
except ImportError:
    # Fallback for direct execution context adjustments
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from code.utils.logging import get_logger, log_error, log_info, log_warning
    from code.utils.checksum import compute_file_sha256, compute_and_store_checksum

logger = get_logger(__name__)

# Constants
PROJECT_ID = "PROJ-485"
STATE_DIR = os.path.join("state", PROJECT_ID)
STATE_FILE = os.path.join(STATE_DIR, "pipeline_state.yaml")

# Pipeline Steps Definition
# Order matters. These correspond to the implementation tasks in tasks.md.
PIPELINE_STEPS = [
    {
        "id": "ingest",
        "name": "Data Ingestion",
        "module": "code.ingest.load_data",
        "function": "run_ingestion",
        "description": "Load raw data from NIST-JANAF/SGTE or local CSV"
    },
    {
        "id": "features",
        "name": "Feature Generation",
        "module": "code.features.generate_descriptors",
        "function": "run_descriptor_generation",
        "description": "Calculate compositional descriptors"
    },
    {
        "id": "train",
        "name": "Model Training",
        "module": "code.models.train",
        "function": "run_training",
        "description": "Train Random Forest with LOSO CV"
    },
    {
        "id": "viz",
        "name": "Visualization",
        "module": "code.viz.plot_phase_diagrams",
        "function": "run_visualization",
        "description": "Generate phase diagram plots"
    }
]

def load_state() -> Dict[str, Any]:
    """Load the current pipeline state from disk."""
    if not os.path.exists(STATE_FILE):
        logger.info(f"State file {STATE_FILE} not found. Initializing new state.")
        return {
            "project_id": PROJECT_ID,
            "start_time": None,
            "end_time": None,
            "status": "initialized",
            "steps": {},
            "config": {}
        }
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = yaml.safe_load(f)
            if state is None:
                return {"project_id": PROJECT_ID, "status": "empty"}
            return state
    except Exception as e:
        log_error(logger, f"Failed to load state file: {e}")
        return {"project_id": PROJECT_ID, "status": "corrupted"}

def save_state(state: Dict[str, Any]) -> bool:
    """Save the pipeline state to disk."""
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        with open(STATE_FILE, 'w') as f:
            yaml.dump(state, f, default_flow_style=False)
        log_info(logger, f"State saved to {STATE_FILE}")
        return True
    except Exception as e:
        log_error(logger, f"Failed to save state file: {e}")
        return False

def update_step_status(step_id: str, status: str, details: Optional[Dict] = None, state: Optional[Dict] = None) -> Dict:
    """Update the status of a specific step in the state dictionary."""
    if state is None:
        state = load_state()
    
    if "steps" not in state:
        state["steps"] = {}
    
    timestamp = datetime.now().isoformat()
    
    step_info = {
        "step_id": step_id,
        "status": status,
        "started_at": state["steps"].get(step_id, {}).get("started_at"),
        "completed_at": timestamp,
        "details": details or {}
    }
    
    if status == "running":
        step_info["started_at"] = timestamp
        step_info["completed_at"] = None
    
    state["steps"][step_id] = step_info
    state["last_updated"] = timestamp
    
    # Update overall status
    if status == "failed":
        state["status"] = "failed"
    elif status == "completed":
        # Check if all steps are completed
        completed_count = sum(1 for s in state["steps"].values() if s.get("status") == "completed")
        if completed_count == len(PIPELINE_STEPS):
            state["status"] = "completed"
            state["end_time"] = timestamp
        elif state["status"] != "failed":
            state["status"] = "running"
    
    return state

def run_step(step_config: Dict, state: Dict[str, Any]) -> bool:
    """Execute a single pipeline step."""
    step_id = step_config["id"]
    step_name = step_config["name"]
    module_name = step_config["module"]
    func_name = step_config["function"]
    
    logger.info(f"Starting step: {step_name} ({step_id})")
    
    state = update_step_status(step_id, "running", {}, state)
    save_state(state)
    
    try:
        # Dynamic import
        module = __import__(module_name, fromlist=[func_name])
        run_func = getattr(module, func_name)
        
        # Execute the step function
        # We pass the current state to allow steps to read config or previous results if needed
        result = run_func(state)
        
        if result is True or (isinstance(result, dict) and result.get("success", True)):
            logger.info(f"Step {step_name} completed successfully.")
            state = update_step_status(step_id, "completed", result if isinstance(result, dict) else {}, state)
            save_state(state)
            return True
        else:
            raise Exception(f"Step returned failure result: {result}")
            
    except Exception as e:
        log_error(logger, f"Step {step_name} failed with error: {e}", exc_info=True)
        state = update_step_status(step_id, "failed", {"error": str(e)}, state)
        save_state(state)
        return False

def run_pipeline(steps: Optional[List[str]] = None, resume: bool = False) -> bool:
    """
    Execute the full pipeline or a subset of steps.
    
    Args:
        steps: List of step IDs to run. If None, runs all defined steps.
        resume: If True, skips steps already marked as 'completed' in state.
    
    Returns:
        bool: True if pipeline finished successfully, False otherwise.
    """
    state = load_state()
    
    if state.get("status") == "failed" and not resume:
        logger.warning("Previous run failed. Use --resume to continue.")
        return False
    
    if state["status"] != "running" and state["status"] != "initialized":
        state["start_time"] = datetime.now().isoformat()
        state["status"] = "running"
        save_state(state)
    
    steps_to_run = steps if steps else [s["id"] for s in PIPELINE_STEPS]
    
    for step_config in PIPELINE_STEPS:
        if step_config["id"] not in steps_to_run:
            continue
        
        # Check if already completed and we are resuming
        if resume:
            step_state = state.get("steps", {}).get(step_config["id"], {})
            if step_state.get("status") == "completed":
                logger.info(f"Skipping {step_config['name']} (already completed)")
                continue
        
        success = run_step(step_config, state)
        if not success:
            logger.error(f"Pipeline halted at step: {step_config['name']}")
            return False
    
    logger.info("Pipeline execution completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Alloy Phase Diagram Prediction Pipeline")
    parser.add_argument("--steps", nargs="+", help="Specific steps to run (e.g., ingest features)")
    parser.add_argument("--resume", action="store_true", help="Resume from last failed step")
    parser.add_argument("--init", action="store_true", help="Initialize state file only")
    
    args = parser.parse_args()
    
    if args.init:
        state = load_state()
        save_state(state)
        logger.info("State initialized.")
        return
    
    success = run_pipeline(steps=args.steps, resume=args.resume)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()