"""
Logging infrastructure for the Cognitive Fatigue EEG pipeline.

Provides a centralized logger configuration and helper functions to track
participant exclusion and artifact rejection reasons.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Global logger instance
_logger = None

def get_logger(name: str = "eeg_pipeline") -> logging.Logger:
    """
    Get or create the global logger instance with standard configuration.
    
    Args:
        name: Logger name (default: "eeg_pipeline")
        
    Returns:
        Configured logging.Logger instance
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if _logger.handlers:
            return _logger  # Already configured

        _logger.setLevel(logging.DEBUG)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_format)
        _logger.addHandler(console_handler)

        # Create file handler for detailed logs
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_format)
        _logger.addHandler(file_handler)

        # Initialize custom storage lists for rejection tracking
        _logger.rejection_log = []
        _logger.exclusion_log = []

    return _logger

def log_participant_exclusion(
    participant_id: str, 
    reason: str, 
    stage: str = "preprocessing"
) -> None:
    """
    Log a participant exclusion event.
    
    Args:
        participant_id: The ID of the excluded participant
        reason: The reason for exclusion
        stage: The pipeline stage where exclusion occurred
    """
    logger = get_logger()
    exclusion_record = {
        "participant_id": participant_id,
        "reason": reason,
        "stage": stage,
        "timestamp": datetime.now().isoformat()
    }
    logger.warning(f"Participant {participant_id} excluded: {reason} (stage: {stage})")
    
    # Store in custom attribute for later retrieval
    logger.exclusion_log.append(exclusion_record)

def log_artifact_rejection(
    segment_id: str, 
    reason: str, 
    artifact_type: str, 
    threshold: float = None,
    measured_value: float = None
) -> None:
    """
    Log an artifact rejection event for a specific EEG segment.
    
    Args:
        segment_id: The ID of the rejected segment
        reason: The reason for rejection
        artifact_type: Type of artifact (e.g., "amplitude", "line_noise")
        threshold: The threshold that was exceeded (optional)
        measured_value: The measured value that triggered rejection (optional)
    """
    logger = get_logger()
    rejection_record = {
        "segment_id": segment_id,
        "reason": reason,
        "artifact_type": artifact_type,
        "threshold": threshold,
        "measured_value": measured_value,
        "timestamp": datetime.now().isoformat()
    }
    
    log_msg = f"Segment {segment_id} rejected: {reason} ({artifact_type})"
    if threshold is not None and measured_value is not None:
        log_msg += f" [threshold: {threshold}, value: {measured_value}]"
    
    logger.warning(log_msg)
    
    # Store in custom attribute for later retrieval
    logger.rejection_log.append(rejection_record)

def save_rejection_summary(output_path: str = "data/analysis/rejection_summary.json") -> None:
    """
    Save the collected exclusion and rejection logs to a JSON file.
    
    Args:
        output_path: Path to the output JSON file
    """
    logger = get_logger()
    summary = {
        "exclusions": logger.exclusion_log,
        "rejections": logger.rejection_log,
        "generated_at": datetime.now().isoformat()
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Rejection summary saved to {output_path}")

def get_rejection_counts() -> dict:
    """
    Get counts of exclusions and rejections by reason.
    
    Returns:
        Dictionary with counts grouped by reason
    """
    logger = get_logger()
    counts = {
        "exclusions": {},
        "rejections": {}
    }
    
    for record in logger.exclusion_log:
        reason = record.get("reason", "unknown")
        counts["exclusions"][reason] = counts["exclusions"].get(reason, 0) + 1
    
    for record in logger.rejection_log:
        reason = record.get("reason", "unknown")
        counts["rejections"][reason] = counts["rejections"].get(reason, 0) + 1
    
    return counts