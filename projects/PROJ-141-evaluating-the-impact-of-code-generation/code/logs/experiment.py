import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

# Ensure the logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

_logger: Optional[logging.Logger] = None


def timegm(dt: datetime) -> int:
    """
    Convert a datetime object to a Unix timestamp (seconds since epoch).
    Handles timezone-aware and naive datetimes (assumes UTC for naive).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def setup_experiment_logger(
    log_file_name: str = "experiment.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup and return the experiment logger.
    Configures file and console handlers.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("experiment")
    logger.setLevel(level)

    # Prevent adding multiple handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    log_path = LOGS_DIR / log_file_name
    fh = logging.FileHandler(log_path)
    fh.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Formatter: ISO8601 timestamp, level, message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the experiment logger, initializing it if necessary.
    """
    if _logger is None:
        return setup_experiment_logger()
    return _logger


def log_experiment_event(
    event_type: str,
    data: Dict[str, Any],
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log a generic experiment event with structured JSON data.
    
    Args:
        event_type: Type of event (e.g., 'INFO', 'ERROR', 'METRIC')
        data: Dictionary containing event details
        logger: Logger instance (uses default if None)
    """
    if logger is None:
        logger = get_logger()
    
    log_entry = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    
    # Log as JSON string for machine readability
    logger.info(json.dumps(log_entry))


def log_condition_assignment(
    participant_id: str,
    condition: str,
    seed: int,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log the condition assignment for a participant.
    FR-012 requirement: Record participant IDs, condition assignments, and seeds.
    
    Args:
        participant_id: Unique identifier for the participant
        condition: Assigned condition (e.g., 'LLM-assisted', 'baseline')
        seed: Random seed used for assignment
        logger: Logger instance (uses default if None)
    """
    if logger is None:
        logger = get_logger()
    
    data = {
        "participant_id": participant_id,
        "condition": condition,
        "seed": seed,
        "assignment_time": datetime.now(timezone.utc).isoformat()
    }
    
    log_experiment_event("CONDITION_ASSIGNMENT", data, logger)


def log_consent(
    participant_id: str,
    consent_status: str,
    irb_approval_id: str,
    consent_hash: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log the consent status for a participant.
    
    Args:
        participant_id: Unique identifier for the participant
        consent_status: Status (e.g., 'granted', 'denied', 'expired')
        irb_approval_id: IRB approval ID
        consent_hash: Hash of the consent record
        logger: Logger instance (uses default if None)
    """
    if logger is None:
        logger = get_logger()
    
    data = {
        "participant_id": participant_id,
        "consent_status": consent_status,
        "irb_approval_id": irb_approval_id,
        "consent_hash": consent_hash,
        "consent_time": datetime.now(timezone.utc).isoformat()
    }
    
    log_experiment_event("CONSENT", data, logger)


def log_session_start(
    participant_id: str,
    session_id: str,
    problem_id: str,
    condition: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log the start of an experiment session.
    
    Args:
        participant_id: Unique identifier for the participant
        session_id: Unique identifier for the session
        problem_id: Identifier for the problem being presented
        condition: Current condition (LLM-assisted or baseline)
        logger: Logger instance (uses default if None)
    """
    if logger is None:
        logger = get_logger()
    
    data = {
        "participant_id": participant_id,
        "session_id": session_id,
        "problem_id": problem_id,
        "condition": condition,
        "session_start_time": datetime.now(timezone.utc).isoformat()
    }
    
    log_experiment_event("SESSION_START", data, logger)


def log_session_complete(
    participant_id: str,
    session_id: str,
    duration_seconds: float,
    submission_count: int,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log the completion of an experiment session.
    
    Args:
        participant_id: Unique identifier for the participant
        session_id: Unique identifier for the session
        duration_seconds: Duration of the session in seconds
        submission_count: Number of submissions made
        logger: Logger instance (uses default if None)
    """
    if logger is None:
        logger = get_logger()
    
    data = {
        "participant_id": participant_id,
        "session_id": session_id,
        "duration_seconds": duration_seconds,
        "submission_count": submission_count,
        "session_end_time": datetime.now(timezone.utc).isoformat()
    }
    
    log_experiment_event("SESSION_COMPLETE", data, logger)


def main():
    """
    Main function to demonstrate the logging infrastructure.
    Simulates a participant flow: consent -> condition assignment -> session start -> session complete.
    """
    logger = setup_experiment_logger()
    
    # Simulate participant flow
    participant_id = "P001"
    session_id = "S001"
    problem_id = "HumanEval-001"
    condition = "LLM-assisted"
    seed = 42
    
    # Log consent
    log_consent(
        participant_id=participant_id,
        consent_status="granted",
        irb_approval_id="IRB-2024-001",
        consent_hash="abc123def456",
        logger=logger
    )
    
    # Log condition assignment
    log_condition_assignment(
        participant_id=participant_id,
        condition=condition,
        seed=seed,
        logger=logger
    )
    
    # Log session start
    log_session_start(
        participant_id=participant_id,
        session_id=session_id,
        problem_id=problem_id,
        condition=condition,
        logger=logger
    )
    
    # Simulate session work (sleep for 1 second)
    time.sleep(1)
    
    # Log session complete
    log_session_complete(
        participant_id=participant_id,
        session_id=session_id,
        duration_seconds=1.0,
        submission_count=1,
        logger=logger
    )
    
    logger.info("Experiment logging demonstration complete.")


if __name__ == "__main__":
    main()