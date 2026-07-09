"""
Interaction Logger Module

Handles logging of participant interactions, including dropout detection and
partial data flagging as per US1 requirements.
"""

import os
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from utils.models import InteractionLog
from utils.logging_utils import get_logger

# Constants
DEFAULT_LOG_PATH = Path("data/interaction_logs/raw_logs.csv")
DROPOUT_THRESHOLD_MS = 300000  # 5 minutes of inactivity to flag as potential dropout
MAX_TASKS_PER_PARTICIPANT = 3  # Expected number of tasks per participant based on Latin-square design

logger = get_logger(__name__)


def setup_logger(name: str = "interaction_logger") -> logging.Logger:
    """Setup logger for interaction logging module."""
    return get_logger(name)


def load_raw_logs(log_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load existing raw logs from CSV file.

    Args:
        log_path: Path to the raw logs CSV file. Defaults to DEFAULT_LOG_PATH.

    Returns:
        List of log entries as dictionaries.
    """
    if log_path is None:
        log_path = DEFAULT_LOG_PATH

    if not log_path.exists():
        logger.info(f"No existing log file found at {log_path}. Starting fresh.")
        return []

    logs = []
    try:
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert timestamp back to datetime object if needed
                if 'timestamp_ms' in row:
                    row['timestamp_ms'] = int(row['timestamp_ms'])
                logs.append(row)
        logger.info(f"Loaded {len(logs)} existing log entries from {log_path}")
    except Exception as e:
        logger.error(f"Error loading raw logs from {log_path}: {e}")
        raise

    return logs


def save_raw_logs(logs: List[Dict[str, Any]], log_path: Optional[Path] = None) -> None:
    """
    Save raw logs to CSV file.

    Args:
        logs: List of log entries to save.
        log_path: Path to the raw logs CSV file. Defaults to DEFAULT_LOG_PATH.
    """
    if log_path is None:
        log_path = DEFAULT_LOG_PATH

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'participant_id', 'task_id', 'condition', 'timestamp_ms',
        'selected_line', 'ground_truth_line', 'dropout_flag', 'partial_data_flag'
    ]

    try:
        with open(log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(logs)
        logger.info(f"Saved {len(logs)} log entries to {log_path}")
    except Exception as e:
        logger.error(f"Error saving raw logs to {log_path}: {e}")
        raise


def log_interaction(
    participant_id: str,
    task_id: str,
    condition: str,
    selected_line: int,
    ground_truth_line: int,
    timestamp_ms: Optional[int] = None,
    log_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Log a single participant interaction.

    Args:
        participant_id: Unique identifier for the participant.
        task_id: Unique identifier for the task.
        condition: Experimental condition (e.g., 'baseline', 'llm', 'rule').
        selected_line: Line number selected by the participant.
        ground_truth_line: Actual line number containing the bug.
        timestamp_ms: Timestamp in milliseconds. Defaults to current time.
        log_path: Path to the log file. Defaults to DEFAULT_LOG_PATH.

    Returns:
        The created log entry as a dictionary.
    """
    if timestamp_ms is None:
        timestamp_ms = int(datetime.now().timestamp() * 1000)

    log_entry = {
        'participant_id': participant_id,
        'task_id': task_id,
        'condition': condition,
        'timestamp_ms': timestamp_ms,
        'selected_line': selected_line,
        'ground_truth_line': ground_truth_line,
        'dropout_flag': False,
        'partial_data_flag': False
    }

    # Load existing logs, append new entry, and save
    existing_logs = load_raw_logs(log_path)
    existing_logs.append(log_entry)
    save_raw_logs(existing_logs, log_path)

    logger.debug(f"Logged interaction: participant={participant_id}, task={task_id}, condition={condition}")
    return log_entry


def detect_dropout(
    participant_id: str,
    logs: Optional[List[Dict[str, Any]]] = None,
    log_path: Optional[Path] = None,
    threshold_ms: int = DROPOUT_THRESHOLD_MS
) -> List[Dict[str, Any]]:
    """
    Detect potential dropouts for a participant based on inactivity.

    A dropout is flagged if:
    1. The participant has started tasks but has not completed all expected tasks.
    2. There is a gap > threshold_ms between consecutive interactions.

    Args:
        participant_id: Unique identifier for the participant.
        logs: Existing logs to analyze. If None, loads from log_path.
        log_path: Path to the log file. Defaults to DEFAULT_LOG_PATH.
        threshold_ms: Inactivity threshold in milliseconds.

    Returns:
        List of log entries with dropout_flag set to True.
    """
    if logs is None:
        logs = load_raw_logs(log_path)

    # Filter logs for this participant
    participant_logs = [log for log in logs if log['participant_id'] == participant_id]

    if not participant_logs:
        logger.info(f"No logs found for participant {participant_id}")
        return []

    # Sort by timestamp
    participant_logs.sort(key=lambda x: x['timestamp_ms'])

    dropout_entries = []

    # Check for inactivity gaps
    for i in range(1, len(participant_logs)):
        prev_time = participant_logs[i-1]['timestamp_ms']
        curr_time = participant_logs[i]['timestamp_ms']
        gap = curr_time - prev_time

        if gap > threshold_ms:
            # Flag the current entry as potential dropout
            participant_logs[i]['dropout_flag'] = True
            dropout_entries.append(participant_logs[i])
            logger.warning(
                f"Potential dropout detected for participant {participant_id}: "
                f"inactivity gap of {gap/1000:.1f}s between tasks"
            )

    # Check for incomplete task sets (partial data)
    expected_tasks = set()
    # Assuming each participant does 3 tasks (one per condition) based on Latin-square design
    # This could be made configurable if needed
    conditions = ['baseline', 'llm', 'rule']
    for condition in conditions:
        # We expect at least one task per condition, but task_id might vary
        # For now, we check if we have interactions for all conditions
        pass

    # Simpler check: if participant has logs but hasn't completed all expected conditions
    conditions_seen = set(log['condition'] for log in participant_logs)
    if len(conditions_seen) < len(conditions) and len(participant_logs) > 0:
        # Flag the last entry as partial data
        if participant_logs:
            participant_logs[-1]['partial_data_flag'] = True
            dropout_entries.append(participant_logs[-1])
            logger.warning(
                f"Partial data detected for participant {participant_id}: "
                f"only {len(conditions_seen)}/{len(conditions)} conditions completed"
            )

    return dropout_entries


def flag_partial_data(
    participant_id: str,
    logs: Optional[List[Dict[str, Any]]] = None,
    log_path: Optional[Path] = None,
    max_tasks: int = MAX_TASKS_PER_PARTICIPANT
) -> List[Dict[str, Any]]:
    """
    Flag participants with partial data (incomplete task sets).

    Args:
        participant_id: Unique identifier for the participant.
        logs: Existing logs to analyze. If None, loads from log_path.
        log_path: Path to the log file. Defaults to DEFAULT_LOG_PATH.
        max_tasks: Expected number of tasks per participant.

    Returns:
        List of log entries with partial_data_flag set to True.
    """
    if logs is None:
        logs = load_raw_logs(log_path)

    # Filter logs for this participant
    participant_logs = [log for log in logs if log['participant_id'] == participant_id]

    if not participant_logs:
        return []

    # Count unique tasks completed
    tasks_completed = len(set(log['task_id'] for log in participant_logs))
    conditions_completed = len(set(log['condition'] for log in participant_logs))

    # Flag if incomplete
    partial_entries = []
    if tasks_completed < max_tasks or conditions_completed < 3:
        # Flag the last entry as partial data
        participant_logs[-1]['partial_data_flag'] = True
        partial_entries.append(participant_logs[-1])
        logger.warning(
            f"Partial data flagged for participant {participant_id}: "
            f"{tasks_completed}/{max_tasks} tasks, {conditions_completed}/3 conditions completed"
        )

    return partial_entries


def get_participant_summary(
    participant_id: str,
    logs: Optional[List[Dict[str, Any]]] = None,
    log_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a summary for a participant's data quality.

    Args:
        participant_id: Unique identifier for the participant.
        logs: Existing logs to analyze. If None, loads from log_path.
        log_path: Path to the log file. Defaults to DEFAULT_LOG_PATH.

    Returns:
        Dictionary with participant data quality summary.
    """
    if logs is None:
        logs = load_raw_logs(log_path)

    participant_logs = [log for log in logs if log['participant_id'] == participant_id]

    if not participant_logs:
        return {
            'participant_id': participant_id,
            'total_interactions': 0,
            'dropout_detected': False,
            'partial_data_detected': False,
            'conditions_completed': 0,
            'tasks_completed': 0,
            'status': 'no_data'
        }

    dropout_count = sum(1 for log in participant_logs if log.get('dropout_flag', False))
    partial_count = sum(1 for log in participant_logs if log.get('partial_data_flag', False))
    conditions = set(log['condition'] for log in participant_logs)
    tasks = set(log['task_id'] for log in participant_logs)

    status = 'complete'
    if dropout_count > 0:
        status = 'dropout'
    elif partial_count > 0 or len(conditions) < 3:
        status = 'partial'

    return {
        'participant_id': participant_id,
        'total_interactions': len(participant_logs),
        'dropout_detected': dropout_count > 0,
        'partial_data_detected': partial_count > 0,
        'conditions_completed': len(conditions),
        'tasks_completed': len(tasks),
        'status': status
    }


def process_all_participants(
    log_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Process all participants in the log file to detect dropouts and partial data.

    Args:
        log_path: Path to the raw logs CSV file. Defaults to DEFAULT_LOG_PATH.
        output_path: Path to save the updated logs. Defaults to log_path.

    Returns:
        Dictionary with processing summary.
    """
    if log_path is None:
        log_path = DEFAULT_LOG_PATH

    if not log_path.exists():
        logger.warning(f"No log file found at {log_path}. Nothing to process.")
        return {'processed': 0, 'dropouts': 0, 'partial': 0}

    logs = load_raw_logs(log_path)
    participants = set(log['participant_id'] for log in logs)

    dropout_count = 0
    partial_count = 0

    for participant_id in participants:
        # Detect dropouts
        dropouts = detect_dropout(participant_id, logs, log_path=None)
        dropout_count += len(dropouts)

        # Flag partial data
        partials = flag_partial_data(participant_id, logs, log_path=None)
        partial_count += len(partials)

    # Save updated logs
    if output_path is None:
        output_path = log_path

    save_raw_logs(logs, output_path)

    summary = {
        'processed': len(participants),
        'dropouts': dropout_count,
        'partial': partial_count,
        'total_interactions': len(logs)
    }

    logger.info(f"Processed {summary['processed']} participants: "
               f"{summary['dropouts']} dropouts, {summary['partial']} partial data entries")

    return summary


def main():
    """Main entry point for dropout handling and partial data flagging."""
    logger.info("Starting interaction logger dropout analysis...")

    # Process all participants
    result = process_all_participants()

    # Print summary
    print(f"\nDropout and Partial Data Analysis Summary:")
    print(f"  Participants processed: {result['processed']}")
    print(f"  Dropouts detected: {result['dropouts']}")
    print(f"  Partial data entries: {result['partial']}")
    print(f"  Total interactions: {result['total_interactions']}")

    # Show detailed status for each participant
    logs = load_raw_logs()
    participants = set(log['participant_id'] for log in logs)

    print("\nParticipant Status:")
    for participant_id in sorted(participants):
        summary = get_participant_summary(participant_id, logs)
        print(f"  {participant_id}: {summary['status']} "
             f"({summary['conditions_completed']}/3 conditions, "
             f"{summary['tasks_completed']} tasks)")

    logger.info("Interaction logger dropout analysis complete.")


if __name__ == "__main__":
    main()