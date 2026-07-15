import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config.loader import load_config
from utils.logger import get_memory_log_path, get_memory_log

logger = logging.getLogger(__name__)

STATE_DIR = Path("state")
STATUS_FILE = STATE_DIR / "execution_status.json"

def ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_status() -> Dict[str, Any]:
    """Load existing status file or return a default structure."""
    ensure_state_dir()
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load status file {STATUS_FILE}: {e}. Starting fresh.")
            return {"pipeline_version": "1.0", "tasks": {}, "last_updated": None}
    return {
        "pipeline_version": "1.0",
        "tasks": {},
        "last_updated": None,
        "memory_logs": [],
        "final_report_path": None
    }

def save_status(status: Dict[str, Any]) -> None:
    """Save the status dictionary to the JSON file."""
    ensure_state_dir()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, default=str)
    logger.info(f"Status saved to {STATUS_FILE}")

def update_task_status(task_id: str, status: str, details: Optional[str] = None) -> None:
    """Update the status of a specific task in the state file."""
    status_data = load_status()
    status_data["tasks"][task_id] = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    status_data["last_updated"] = datetime.now().isoformat()
    save_status(status_data)

def update_execution_summary(
    total_tasks: int,
    completed_tasks: int,
    failed_tasks: int,
    execution_time_seconds: Optional[float] = None
) -> None:
    """Update the global execution summary in the state file."""
    status_data = load_status()
    status_data["summary"] = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "execution_time_seconds": execution_time_seconds,
        "status": "completed" if failed_tasks == 0 else "completed_with_errors"
    }
    status_data["last_updated"] = datetime.now().isoformat()
    save_status(status_data)

def update_memory_logs() -> None:
    """Read the memory log from utils.logger and append it to the state file."""
    status_data = load_status()
    memory_log_path = get_memory_log_path()
    memory_data = get_memory_log()
    
    if memory_data:
        status_data["memory_logs"] = memory_data
        logger.info(f"Memory logs updated from {memory_log_path}")
    else:
        logger.warning("No memory data found to update.")
    
    status_data["last_updated"] = datetime.now().isoformat()
    save_status(status_data)

def update_final_report_path(report_path: str) -> None:
    """Update the final report path in the state file."""
    status_data = load_status()
    status_data["final_report_path"] = report_path
    status_data["last_updated"] = datetime.now().isoformat()
    save_status(status_data)
    logger.info(f"Final report path updated to: {report_path}")

def run_status_update_pipeline(
    task_id: str,
    task_status: str,
    task_details: Optional[str] = None,
    report_path: Optional[str] = None,
    total_tasks: Optional[int] = None,
    completed_tasks: Optional[int] = None,
    failed_tasks: Optional[int] = None,
    execution_time: Optional[float] = None
) -> None:
    """
    Orchestrates the update of the state file with:
    1. Specific task status
    2. Memory logs
    3. Final report path (if provided)
    4. Global execution summary (if stats provided)
    """
    logger.info(f"Updating state for task {task_id} with status {task_status}")
    
    # Update specific task
    update_task_status(task_id, task_status, task_details)
    
    # Update memory logs
    update_memory_logs()
    
    # Update final report path if provided
    if report_path:
        update_final_report_path(report_path)
    
    # Update summary if stats provided
    if total_tasks is not None and completed_tasks is not None and failed_tasks is not None:
        update_execution_summary(total_tasks, completed_tasks, failed_tasks, execution_time)

if __name__ == "__main__":
    # Example usage for manual testing
    logging.basicConfig(level=logging.INFO)
    run_status_update_pipeline(
        task_id="T041",
        task_status="completed",
        task_details="State file updated successfully.",
        report_path="data/reports/final_report.html",
        total_tasks=44,
        completed_tasks=44,
        failed_tasks=0,
        execution_time=1200.5
    )
