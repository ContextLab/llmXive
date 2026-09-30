import os
import sys
import argparse
import json
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logging import get_logger, log_info, log_error
from utils.error_codes import ErrorCode
from utils.resource_monitor import resource_monitor_wrapper

logger = get_logger(__name__)

def ensure_state_directory():
    state_dir = "state/PROJ-485"
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def load_state(state_path):
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    return {"steps": {}, "artifacts": {}}

def save_state(state_path, state):
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

def update_step_status(state, step_name, status, details=None):
    state["steps"][step_name] = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    return state

@resource_monitor_wrapper(resource_log_path="data/artifacts/resource_log.json")
def run_pipeline():
    """
    Orchestrates the full pipeline execution.
    This function is wrapped by the resource monitor to track execution time and memory.
    """
    logger.info("Starting pipeline execution...")
    
    # 1. Setup Directories
    logger.info("Step 1: Ensuring directories exist...")
    ensure_state_directory()
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/artifacts", exist_ok=True)
    os.makedirs("data/logs", exist_ok=True)

    # 2. Seed Elemental Properties (T007)
    logger.info("Step 2: Seeding elemental properties...")
    from features.seed_elemental_properties import main as seed_main
    seed_main()

    # 3. Load Data (T012-T015)
    logger.info("Step 3: Loading data...")
    from ingest.load_data import main as load_main
    load_main()

    # 4. Generate Descriptors (T017-T020)
    logger.info("Step 4: Generating descriptors...")
    from features.generate_descriptors import main as gen_desc_main
    gen_desc_main()

    # 5. Train Model (T022-T031)
    logger.info("Step 5: Training model...")
    from models.train import main as train_main
    train_main()

    # 6. Evaluate Model (T028-T029)
    logger.info("Step 6: Evaluating model...")
    from models.evaluate import main as eval_main
    eval_main()

    # 7. Visualization (T032-T040)
    logger.info("Step 7: Generating visualizations...")
    from viz.plot_phase_diagrams import main as viz_main
    viz_main()

    logger.info("Pipeline execution completed successfully.")
    return "success"

def run_step(step_name):
    """Run a specific step of the pipeline."""
    logger.info(f"Running step: {step_name}")
    # Implementation for specific steps would go here
    pass

def main():
    parser = argparse.ArgumentParser(description="Alloy Phase Diagram Prediction Pipeline")
    parser.add_argument("--step", type=str, help="Specific step to run")
    args = parser.parse_args()

    state_path = "state/PROJ-485/pipeline_state.json"
    state = load_state(state_path)

    try:
        if args.step:
            run_step(args.step)
        else:
            run_pipeline()
        
        state = update_step_status(state, "pipeline_complete", "success")
        save_state(state_path, state)
        
    except Exception as e:
        log_error("MAIN", f"Pipeline failed: {e}")
        state = update_step_status(state, "pipeline_complete", "failed", {"error": str(e)})
        save_state(state_path, state)
        sys.exit(1)

if __name__ == "__main__":
    main()