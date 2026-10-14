"""
Main entry point for the llmXive pipeline.
Orchestrates task execution based on code/dag.yaml.
"""
import argparse
import sys
import logging
import yaml
import time
import importlib
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("llmXive.main")

class DAGExecutionError(Exception):
    """Raised when a task in the DAG fails to execute."""
    pass

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="llmXive Pipeline Executor")
    parser.add_argument(
        "--phase",
        type=str,
        default=None,
        help="Run only a specific phase (e.g., 'us1', 'us2'). If None, runs full pipeline."
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Run only a specific task ID (e.g., 'T015')."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to configuration file."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        help="Model identifier to use for inference."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to run inference on (cpu, cuda)."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Global timeout in seconds."
    )
    # New generic sample flag – accepted by the pipeline but not used directly.
    parser.add_argument(
        "--sample",
        type=str,
        default="full",
        help="Sample size hint (e.g., 'small', 'full'). Used by downstream scripts."
    )
    return parser.parse_args()

def load_dag(dag_path: str = "code/dag.yaml") -> Dict[str, Any]:
    """Load the DAG definition from a YAML file."""
    path = Path(dag_path)
    if not path.exists():
        raise FileNotFoundError(f"DAG file not found at {path}")

    with open(path, 'r') as f:
        dag = yaml.safe_load(f)

    if not dag or 'tasks' not in dag:
        raise ValueError("Invalid DAG format: missing 'tasks' key")

    return dag

def get_task_function(task_id: str) -> Callable:
    """
    Dynamically import and return the main function for a given task ID.
    Maps task IDs to their implementing modules based on tasks.md conventions.
    """
    task_map = {
        # Phase 0
        "T011": ("analysis.feasibility", "main"),
        "T011c": ("analysis.power_sensitivity", "main"),
        # Phase 1: US1
        "T015": ("data.download", "main"),
        "T016": ("data.preprocess", "main"),
        "T011b": ("analysis.variance_check", "main"),
        "T018a": ("data.ngram", "main"),
        "T018b": ("data.ngram", "main"),
        "T017": ("inference.engine", "main"),
        "T019": ("analysis.correlation", "main"),
        "T020": ("analysis.correlation", "main"),
        "T021a": ("main", "parse_args"),
        "T022": ("analysis.correlation", "main"),
        # Phase 2: US2
        "T024": ("analysis.threshold", "main"),
        "T025": ("analysis.threshold", "main"),
        "T026": ("analysis.threshold", "main"),
        "T027": ("analysis.threshold", "main"),
        # Phase 3: US3
        "T029": ("analysis.stats", "main"),
        "T030": ("analysis.stats", "main"),
        "T031": ("analysis.stats", "main"),
        # Phase N
        "T032a": ("setup_directories", "main"),
        "T032b": ("setup_directories", "main"),
        "T034c": ("analysis.threshold", "main"),
    }

    if task_id not in task_map:
        logger.warning(f"No explicit mapping for {task_id}, attempting inference or skipping.")
        raise ValueError(f"Task {task_id} not mapped in get_task_function")

    module_name, func_name = task_map[task_id]

    try:
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        return func
    except ImportError as e:
        logger.error(f"Failed to import module {module_name} for task {task_id}: {e}")
        raise
    except AttributeError as e:
        logger.error(f"Function {func_name} not found in {module_name} for task {task_id}: {e}")
        raise

def execute_task(task_id: str, args: argparse.Namespace) -> bool:
    """
    Execute a single task.
    Returns True on success, False on failure.
    """
    logger.info(f"--- Executing Task: {task_id} ---")
    try:
        func = get_task_function(task_id)

        # Most task entry points are designed to parse their own CLI arguments.
        # We simply invoke the function; if it needs arguments it will read sys.argv.
        func()
        logger.info(f"Task {task_id} completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {e}")
        logger.error(traceback.format_exc())
        return False

def get_tasks_for_phase(phase: str, dag: Dict[str, Any]) -> List[str]:
    """Filter tasks based on phase."""
    phase_map = {
        "us1": ["T011", "T011c", "T015", "T016", "T011b", "T018a", "T018b", "T017", "T019", "T020", "T021a", "T022"],
        "us2": ["T024", "T025", "T026", "T027"],
        "us3": ["T029", "T030", "T031"],
        "setup": ["T001", "T002", "T008a", "T008b", "T008c", "T009b", "T010"],
        "full": None
    }

    if phase == "full" or phase is None:
        return [t["id"] for t in dag["tasks"]]

    if phase not in phase_map:
        logger.warning(f"Unknown phase {phase}. Running all tasks.")
        return [t["id"] for t in dag["tasks"]]

    target_ids = phase_map[phase]
    return [t["id"] for t in dag["tasks"] if t["id"] in target_ids]

def run_phase(phase: str, dag: Dict[str, Any], args: argparse.Namespace) -> bool:
    """Execute all tasks in a specific phase respecting dependencies."""
    tasks = get_tasks_for_phase(phase, dag)
    if not tasks:
        logger.warning(f"No tasks found for phase {phase}")
        return True

    success = True
    for task_id in tasks:
        if not execute_task(task_id, args):
            logger.error(f"Pipeline halted due to failure in {task_id}")
            success = False
            break
    return success

def run_full_pipeline(dag: Dict[str, Any], args: argparse.Namespace) -> bool:
    """Run the entire pipeline."""
    return run_phase("full", dag, args)

def main():
    """Main entry point."""
    args = parse_args()

    # Load DAG
    try:
        dag = load_dag()
    except Exception as e:
        logger.critical(f"Failed to load DAG: {e}")
        sys.exit(1)

    # Determine execution scope
    if args.task:
        success = execute_task(args.task, args)
        sys.exit(0 if success else 1)
    elif args.phase:
        success = run_phase(args.phase, dag, args)
        sys.exit(0 if success else 1)
    else:
        success = run_full_pipeline(dag, args)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()