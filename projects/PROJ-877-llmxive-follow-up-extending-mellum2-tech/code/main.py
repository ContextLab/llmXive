import argparse
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from config import get_project_root, get_config
from setup_directories import ensure_data_directories, generate_init_files
from setup_logging import setup_logger, log_directory_creation

# Import phase-specific entry points from existing modules
# These correspond to the "phases" defined in the DAG
from data.download import main as run_download
from data.preprocess import main as run_preprocess
from data.ngram import main as run_ngram
from inference.engine import main as run_inference
from analysis.feasibility import main as run_feasibility
from analysis.power_sensitivity import main as run_power_sensitivity
from analysis.variance_check import main as run_variance_check
from analysis.correlation import main as run_correlation

logger = logging.getLogger(__name__)

class PipelineError(Exception):
    """Custom exception for pipeline execution errors."""
    pass

def parse_args():
    """Parse command line arguments.
    
    Supports:
      --phase: Pipeline phase to execute (init, download, preprocess, inference, analysis, all)
      --config: Path to configuration file
      --verbose: Enable verbose logging
      --dag: Path to DAG definition file (for orchestration)
    """
    parser = argparse.ArgumentParser(
        description="llmXive Science Pipeline - Main Entry Point"
    )
    parser.add_argument(
        "--phase",
        type=str,
        default="init",
        choices=["init", "download", "preprocess", "inference", "analysis", "all", "dag"],
        help="Pipeline phase to execute"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dag",
        type=str,
        default="code/dag.yaml",
        help="Path to DAG definition file for orchestration"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse arguments and print configuration without executing"
    )
    return parser.parse_args()

def load_dag(dag_path: Path) -> Dict[str, Any]:
    """Load the DAG definition from a YAML file.
    
    Expected structure:
    tasks:
      - id: task_id
        name: human_readable_name
        command: "module:function" or "phase_name"
        dependencies: ["task_id_1", "task_id_2"]
        parallel: false
    """
    if not dag_path.exists():
        raise FileNotFoundError(f"DAG file not found: {dag_path}")
    
    with open(dag_path, 'r') as f:
        return yaml.safe_load(f)

def get_task_function(task_id: str, dag: Dict[str, Any]) -> Callable:
    """Map a task ID to its execution function based on the DAG definition."""
    # Map task IDs to the actual functions imported at the top of this file
    # This mapping is derived from the task list in tasks.md
    task_map = {
        "T011": run_feasibility,
        "T011c": run_power_sensitivity,
        "T015": run_download,
        "T016": run_preprocess,
        "T011b": run_variance_check,
        "T018a": run_ngram, # Note: ngram.py handles both python and java via args/config
        "T018b": run_ngram, # Same function, different invocation context
        "T017": run_inference,
        "T019": run_correlation,
        "T020": run_correlation, # Visualization is part of correlation module
        "T021a": lambda: 0, # CLI parsing is handled here
    }
    
    # If the task is a specific phase like "download", we might need to route differently
    # But the DAG usually lists specific task IDs.
    if task_id in task_map:
        return task_map[task_id]
    
    # Fallback: try to find a phase name if the task ID isn't mapped directly
    # This handles cases where the DAG might just say "phase: download"
    phase_map = {
        "download": run_download,
        "preprocess": run_preprocess,
        "ngram": run_ngram,
        "inference": run_inference,
        "correlation": run_correlation,
        "feasibility": run_feasibility,
        "variance": run_variance_check,
        "power_sensitivity": run_power_sensitivity,
    }
    
    # Check if the task_id matches a phase key
    for key, func in phase_map.items():
        if key in task_id.lower():
            return func
    
    raise PipelineError(f"No execution function found for task: {task_id}")

def execute_task(task: Dict[str, Any], dag: Dict[str, Any], completed_tasks: Dict[str, bool]) -> bool:
    """Execute a single task, ensuring dependencies are met."""
    task_id = task.get("id")
    if not task_id:
        raise PipelineError("Task missing 'id' field")
    
    if completed_tasks.get(task_id):
        logger.info(f"Task {task_id} already completed, skipping.")
        return True

    # Check dependencies
    dependencies = task.get("dependencies", [])
    for dep_id in dependencies:
        if not completed_tasks.get(dep_id):
            logger.warning(f"Task {task_id} waiting for dependency {dep_id}")
            return False # Not ready yet

    logger.info(f"Executing task: {task_id} ({task.get('name', 'Unnamed')})")
    
    try:
        func = get_task_function(task_id, dag)
        # Call the function. Most main() functions in this project return 0 on success.
        # We pass sys.argv or specific args if needed, but for now assume default behavior
        # or that the function reads its own config.
        result = func()
        
        if result != 0 and result is not None:
            raise PipelineError(f"Task {task_id} failed with exit code {result}")
        
        completed_tasks[task_id] = True
        logger.info(f"Task {task_id} completed successfully.")
        return True
    
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        raise PipelineError(f"Task {task_id} execution failed: {e}")

def run_dag_execution(dag_path: Path, verbose: bool = False):
    """Run the pipeline according to the DAG definition."""
    level = logging.DEBUG if verbose else logging.INFO
    setup_logger("main", level=level)
    
    dag = load_dag(dag_path)
    tasks = dag.get("tasks", [])
    
    if not tasks:
        logger.warning("No tasks found in DAG.")
        return 0
    
    completed_tasks: Dict[str, bool] = {}
    max_iterations = len(tasks) * 2 # Safety against infinite loops
    iteration = 0
    
    while len(completed_tasks) < len(tasks) and iteration < max_iterations:
        iteration += 1
        made_progress = False
        
        for task in tasks:
            task_id = task.get("id")
            if task_id in completed_tasks:
                continue
            
            try:
                if execute_task(task, dag, completed_tasks):
                    made_progress = True
            except PipelineError as e:
                logger.error(f"Pipeline halted due to error: {e}")
                return 1
        
        if not made_progress:
            # Check if there are remaining tasks that are stuck
            pending = [t for t in tasks if t.get("id") not in completed_tasks]
            if pending:
                logger.error("Deadlock detected: Pending tasks have unmet dependencies.")
                for p in pending:
                    logger.error(f"  Pending: {p.get('id')}, deps: {p.get('dependencies')}")
                return 1
            break
    
    logger.info(f"Pipeline execution complete. {len(completed_tasks)}/{len(tasks)} tasks finished.")
    return 0

def run_init_phase(project_root: Path, verbose: bool = False):
    """Run the initialization phase: create directories and logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logger("main", level=level)
    
    logger.info(f"Running initialization phase for project: {project_root}")
    
    # Create directories
    dirs = ensure_data_directories(project_root)
    
    # Create init files
    init_files = generate_init_files(project_root)
    
    # Log the creation
    log_file = project_root / "project_subdirs_init.log"
    log_directory_creation(project_root, dirs, log_file=log_file)
    
    logger.info(f"Initialization complete. Created {len(dirs)} directories.")
    return 0

def run_pipeline_phase(phase: str, project_root: Path):
    """Run a specific pipeline phase (legacy support)."""
    logger.info(f"Running phase: {phase}")
    
    # Map phase names to functions
    phase_map = {
        "download": run_download,
        "preprocess": run_preprocess,
        "inference": run_inference,
        "analysis": run_correlation,
    }
    
    if phase in phase_map:
        try:
            result = phase_map[phase]()
            if result != 0 and result is not None:
                logger.error(f"Phase {phase} failed.")
                return 1
            return 0
        except Exception as e:
            logger.error(f"Phase {phase} failed: {e}")
            return 1
    else:
        logger.warning(f"Unknown phase: {phase}")
        return 0

def main():
    """Main entry point for the pipeline."""
    args = parse_args()
    
    if args.dry_run:
        print(f"Dry run: phase={args.phase}, config={args.config}, verbose={args.verbose}, dag={args.dag}")
        return 0
    
    try:
        config = get_config()
        project_root = get_project_root(config)
        
        if not project_root.exists():
            project_root.mkdir(parents=True)
        
        if args.phase == "init":
            return run_init_phase(project_root, args.verbose)
        elif args.phase == "dag":
            # Execute the DAG defined in code/dag.yaml
            dag_path = Path(args.dag)
            if not dag_path.is_absolute():
                dag_path = project_root / dag_path
            return run_dag_execution(dag_path, args.verbose)
        elif args.phase == "all":
            # Run init first
            run_init_phase(project_root, args.verbose)
            # Then run the full DAG if available, otherwise run phases sequentially
            dag_path = Path(args.dag)
            if not dag_path.is_absolute():
                dag_path = project_root / dag_path
            
            if dag_path.exists():
                logger.info("DAG file found, executing via DAG.")
                return run_dag_execution(dag_path, args.verbose)
            else:
                logger.warning("DAG file not found, running phases sequentially.")
                for phase in ["download", "preprocess", "inference", "analysis"]:
                    if run_pipeline_phase(phase, project_root) != 0:
                        return 1
                return 0
        else:
            return run_pipeline_phase(args.phase, project_root)
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())