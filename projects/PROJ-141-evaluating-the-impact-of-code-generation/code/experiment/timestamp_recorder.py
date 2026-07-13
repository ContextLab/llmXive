"""
Timestamp recording module for the experiment.
Provides high-precision UTC timestamp recording for experiment events.
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from logs.experiment import get_logger, log_experiment_event

# Configure logger for this module
logger = get_logger("timestamp_recorder")


def get_current_utc_timestamp() -> str:
    """
    Get the current timestamp in UTC format with at least 1 second precision.
    
    Returns:
        str: ISO 8601 formatted timestamp in UTC (e.g., "2024-01-15T14:30:45.123456+00:00")
    """
    now = datetime.now(timezone.utc)
    return now.isoformat()


def get_current_utc_timestamp_unix() -> float:
    """
    Get the current timestamp as a Unix timestamp (seconds since epoch).
    
    Returns:
        float: Unix timestamp with microsecond precision
    """
    now = datetime.now(timezone.utc)
    return now.timestamp()


def record_timestamp(
    participant_id: str,
    session_id: str,
    event_type: str,
    problem_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Record a timestamped event in the experiment log.
    
    Args:
        participant_id: Unique identifier for the participant
        session_id: Unique identifier for the session
        event_type: Type of event being recorded (e.g., "problem_viewed", "code_submitted")
        problem_id: Optional problem identifier
        metadata: Optional additional metadata to include with the timestamp
        
    Returns:
        str: The generated timestamp record ID
    """
    timestamp = get_current_utc_timestamp()
    timestamp_unix = get_current_utc_timestamp_unix()
    
    record_id = str(uuid.uuid4())
    
    log_entry = {
        "record_id": record_id,
        "participant_id": participant_id,
        "session_id": session_id,
        "event_type": event_type,
        "timestamp_utc": timestamp,
        "timestamp_unix": timestamp_unix,
        "problem_id": problem_id,
        "metadata": metadata or {}
    }
    
    # Log the event using the experiment logging infrastructure
    log_experiment_event(
        participant_id=participant_id,
        session_id=session_id,
        event_type=event_type,
        data=log_entry
    )
    
    logger.info(
        f"Recorded timestamp: {event_type} for participant {participant_id}, "
        f"session {session_id}, problem {problem_id}, time={timestamp}"
    )
    
    return record_id


def record_problem_view(
    participant_id: str,
    session_id: str,
    problem_id: str,
    problem_source: str
) -> str:
    """
    Record when a participant views a problem.
    
    Args:
        participant_id: Unique identifier for the participant
        session_id: Unique identifier for the session
        problem_id: The problem being viewed
        problem_source: Source of the problem (e.g., "HumanEval", "Codeforces")
        
    Returns:
        str: The generated timestamp record ID
    """
    return record_timestamp(
        participant_id=participant_id,
        session_id=session_id,
        event_type="problem_viewed",
        problem_id=problem_id,
        metadata={"problem_source": problem_source}
    )


def record_code_submission(
    participant_id: str,
    session_id: str,
    problem_id: str,
    submission_id: str,
    language: str,
    condition: str
) -> str:
    """
    Record when a participant submits code.
    
    Args:
        participant_id: Unique identifier for the participant
        session_id: Unique identifier for the session
        problem_id: The problem being solved
        submission_id: Unique identifier for this submission
        language: Programming language of the submission
        condition: Experimental condition (e.g., "LLM-assisted", "baseline")
        
    Returns:
        str: The generated timestamp record ID
    """
    return record_timestamp(
        participant_id=participant_id,
        session_id=session_id,
        event_type="code_submitted",
        problem_id=problem_id,
        metadata={
            "submission_id": submission_id,
            "language": language,
            "condition": condition
        }
    )


def record_condition_switch(
    participant_id: str,
    session_id: str,
    old_condition: str,
    new_condition: str
) -> str:
    """
    Record when a participant switches conditions.
    
    Args:
        participant_id: Unique identifier for the participant
        session_id: Unique identifier for the session
        old_condition: Previous experimental condition
        new_condition: New experimental condition
        
    Returns:
        str: The generated timestamp record ID
    """
    return record_timestamp(
        participant_id=participant_id,
        session_id=session_id,
        event_type="condition_switch",
        metadata={
            "old_condition": old_condition,
            "new_condition": new_condition
        }
    )


def get_elapsed_time(start_timestamp: str, end_timestamp: str) -> float:
    """
    Calculate elapsed time between two timestamps in seconds.
    
    Args:
        start_timestamp: ISO 8601 formatted start timestamp
        end_timestamp: ISO 8601 formatted end timestamp
        
    Returns:
        float: Elapsed time in seconds
    """
    start_dt = datetime.fromisoformat(start_timestamp)
    end_dt = datetime.fromisoformat(end_timestamp)
    
    return (end_dt - start_dt).total_seconds()


def validate_timestamp_format(timestamp: str) -> bool:
    """
    Validate that a timestamp string is in the correct UTC format.
    
    Args:
        timestamp: Timestamp string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.fromisoformat(timestamp)
        return True
    except ValueError:
        return False


def main():
    """
    Main function to demonstrate timestamp recording functionality.
    This can be used for testing or as a standalone utility.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    print("=== Timestamp Recorder Demo ===")
    
    # Get current timestamp
    current_ts = get_current_utc_timestamp()
    print(f"Current UTC timestamp: {current_ts}")
    
    current_unix = get_current_utc_timestamp_unix()
    print(f"Current Unix timestamp: {current_unix}")
    
    # Validate timestamp format
    is_valid = validate_timestamp_format(current_ts)
    print(f"Timestamp format valid: {is_valid}")
    
    # Record a sample event
    record_id = record_timestamp(
        participant_id="demo_participant_001",
        session_id="demo_session_001",
        event_type="demo_event",
        problem_id="demo_problem_001",
        metadata={"test": True}
    )
    print(f"Recorded event with ID: {record_id}")
    
    # Calculate elapsed time
    start = "2024-01-15T14:30:00+00:00"
    end = "2024-01-15T14:35:30+00:00"
    elapsed = get_elapsed_time(start, end)
    print(f"Elapsed time between {start} and {end}: {elapsed} seconds")
    
    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
