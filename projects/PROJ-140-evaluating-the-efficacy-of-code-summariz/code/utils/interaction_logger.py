import os
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logging_utils import get_logger
from utils.config_manager import get_config

# Ensure the logger is set up correctly
logger = get_logger(__name__)

def setup_logger(name: str = "interaction_logger") -> logging.Logger:
    """
    Setup a dedicated logger for the interaction logger module.
    Returns a logger instance configured to write to a specific file and console.
    """
    log_dir = Path(get_config().get("data_dir", "data")) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)

def load_raw_logs(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load existing raw interaction logs from a CSV file.
    If the file does not exist, returns an empty list.
    """
    if file_path is None:
        config = get_config()
        file_path = str(Path(config.get("data_dir", "data")) / "interaction_logs" / "raw_logs.csv")

    path = Path(file_path)
    if not path.exists():
        logger.info(f"Raw logs file {file_path} does not exist. Starting fresh.")
        return []

    logs = []
    try:
        with open(path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings back to appropriate types if necessary
                # Ensure timestamp_ms is an integer
                if 'timestamp_ms' in row and row['timestamp_ms']:
                    try:
                        row['timestamp_ms'] = int(row['timestamp_ms'])
                    except ValueError:
                        logger.warning(f"Invalid timestamp_ms value: {row['timestamp_ms']}, skipping row.")
                        continue
                logs.append(row)
    except Exception as e:
        logger.error(f"Error loading raw logs from {file_path}: {e}")
        raise

    return logs

def save_raw_logs(logs: List[Dict[str, Any]], file_path: Optional[str] = None) -> None:
    """
    Save the list of interaction logs to a CSV file.
    Creates the directory if it does not exist.
    """
    if file_path is None:
        config = get_config()
        file_path = str(Path(config.get("data_dir", "data")) / "interaction_logs" / "raw_logs.csv")

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['participant_id', 'task_id', 'condition', 'timestamp_ms', 'selected_line', 'ground_truth_line']

    try:
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for log in logs:
                # Ensure all fields are present and strings for CSV
                row = {k: str(v) if v is not None else '' for k, v in log.items()}
                # Ensure missing keys are filled
                for key in fieldnames:
                    if key not in row:
                        row[key] = ''
                writer.writerow(row)
        logger.info(f"Successfully saved {len(logs)} logs to {file_path}")
    except Exception as e:
        logger.error(f"Error saving raw logs to {file_path}: {e}")
        raise

def log_interaction(
    participant_id: str,
    task_id: str,
    condition: str,
    selected_line: int,
    ground_truth_line: int,
    file_path: Optional[str] = None
) -> None:
    """
    Log a single interaction event to the raw logs CSV.
    This function appends a new row to the existing CSV file.

    Args:
        participant_id: Unique identifier for the participant.
        task_id: Unique identifier for the task.
        condition: The experimental condition (e.g., 'baseline', 'llm_sim', 'rule').
        selected_line: The line number selected by the participant.
        ground_truth_line: The actual buggy line number (ground truth).
        file_path: Optional path to the CSV file. Defaults to config.
    """
    timestamp_ms = int(datetime.now().timestamp() * 1000)

    new_log = {
        'participant_id': participant_id,
        'task_id': task_id,
        'condition': condition,
        'timestamp_ms': timestamp_ms,
        'selected_line': selected_line,
        'ground_truth_line': ground_truth_line
    }

    # Load existing logs
    existing_logs = load_raw_logs(file_path)
    
    # Append new log
    existing_logs.append(new_log)
    
    # Save back to file
    save_raw_logs(existing_logs, file_path)

def detect_dropout(logs: List[Dict[str, Any]], expected_tasks_per_participant: int) -> List[str]:
    """
    Detect participants who did not complete all expected tasks.
    
    Args:
        logs: List of interaction log dictionaries.
        expected_tasks_per_participant: Number of tasks each participant should have completed.
    
    Returns:
        List of participant_ids who are considered dropped out (completed < expected tasks).
    """
    participant_tasks = {}
    for log in logs:
        pid = log.get('participant_id')
        if pid:
            if pid not in participant_tasks:
                participant_tasks[pid] = set()
            participant_tasks[pid].add(log.get('task_id'))
    
    dropouts = []
    for pid, tasks in participant_tasks.items():
        if len(tasks) < expected_tasks_per_participant:
            dropouts.append(pid)
            logger.warning(f"Participant {pid} dropped out. Completed {len(tasks)} of {expected_tasks_per_participant} tasks.")
    
    return dropouts

def flag_partial_data(logs: List[Dict[str, Any]], expected_tasks_per_participant: int) -> Dict[str, bool]:
    """
    Flag participants with partial data (dropped out).
    
    Args:
        logs: List of interaction log dictionaries.
        expected_tasks_per_participant: Number of tasks each participant should have completed.
    
    Returns:
        Dictionary mapping participant_id to a boolean (True if partial/dropped out).
    """
    dropouts = detect_dropout(logs, expected_tasks_per_participant)
    return {pid: (pid in dropouts) for pid in set(log.get('participant_id') for log in logs) if pid}

def get_participant_summary(logs: List[Dict[str, Any]], participant_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a summary of interaction logs for a specific participant.
    
    Args:
        logs: List of interaction log dictionaries.
        participant_id: The ID of the participant.
    
    Returns:
        Dictionary with summary statistics or None if not found.
    """
    p_logs = [log for log in logs if log.get('participant_id') == participant_id]
    if not p_logs:
        return None

    total_tasks = len(p_logs)
    conditions = {}
    for log in p_logs:
        cond = log.get('condition', 'unknown')
        if cond not in conditions:
            conditions[cond] = 0
        conditions[cond] += 1

    return {
        'participant_id': participant_id,
        'total_tasks': total_tasks,
        'conditions': conditions,
        'first_log_time': min(log.get('timestamp_ms', 0) for log in p_logs),
        'last_log_time': max(log.get('timestamp_ms', 0) for log in p_logs)
    }

def process_all_participants(file_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Process all logs in the file and return summaries for each participant.
    
    Args:
        file_path: Optional path to the CSV file.
    
    Returns:
        Dictionary mapping participant_id to their summary.
    """
    logs = load_raw_logs(file_path)
    summaries = {}
    
    # Get unique participant IDs
    participant_ids = list(set(log.get('participant_id') for log in logs if log.get('participant_id')))
    
    for pid in participant_ids:
        summaries[pid] = get_participant_summary(logs, pid)
    
    return summaries

def main():
    """
    Main function to demonstrate usage and run basic checks.
    """
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    logs_dir = data_dir / "interaction_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    file_path = logs_dir / "raw_logs.csv"

    # Simulate some logging for demonstration if file is empty
    if not file_path.exists() or file_path.stat().st_size == 0:
        logger.info("Initializing raw_logs.csv with sample data for demonstration.")
        sample_logs = [
            {'participant_id': 'P001', 'task_id': 'T01', 'condition': 'baseline', 'timestamp_ms': 1715623400000, 'selected_line': 45, 'ground_truth_line': 45},
            {'participant_id': 'P001', 'task_id': 'T02', 'condition': 'llm_sim', 'timestamp_ms': 1715623500000, 'selected_line': 12, 'ground_truth_line': 12},
            {'participant_id': 'P002', 'task_id': 'T01', 'condition': 'rule', 'timestamp_ms': 1715623600000, 'selected_line': 30, 'ground_truth_line': 30},
        ]
        save_raw_logs(sample_logs, str(file_path))

    # Load and process
    logs = load_raw_logs(str(file_path))
    print(f"Loaded {len(logs)} interaction logs.")

    # Check for dropouts (assuming 2 tasks per participant for this demo)
    dropouts = detect_dropout(logs, expected_tasks_per_participant=2)
    if dropouts:
        print(f"Detected dropouts: {dropouts}")
    else:
        print("No dropouts detected based on expected tasks per participant.")

    # Generate summaries
    summaries = process_all_participants(str(file_path))
    for pid, summary in summaries.items():
        print(f"Participant {pid}: {summary}")

if __name__ == "__main__":
    main()
