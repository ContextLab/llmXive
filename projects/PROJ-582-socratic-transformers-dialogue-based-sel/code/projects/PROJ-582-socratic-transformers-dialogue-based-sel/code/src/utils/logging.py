"""
Structured logging utility for the Socratic Transformers project.

Handles standard logging and specific edge-case events like
DEGENERATE_DIALOGUE_TRUNCATED as JSON lines for downstream analysis.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Constants for event types
EVENT_DEGENERATE_DIALOGUE_TRUNCATED = "DEGENERATE_DIALOGUE_TRUNCATED"
EVENT_TRAINING_OOM = "TRAINING_OOM"
EVENT_TRAINING_TIMEOUT = "TRAINING_TIMEOUT"
EVENT_DATA_DOWNLOAD_SUCCESS = "DATA_DOWNLOAD_SUCCESS"
EVENT_DATA_DOWNLOAD_FAILURE = "DATA_DOWNLOAD_FAILURE"

class SocraticLogger:
    """
    A structured logger that writes standard logs to stdout/stderr
    and specific edge-case events to a JSON Lines file.
    """

    def __init__(self, name: str = "socratic", log_dir: Optional[Path] = None):
        """
        Initialize the logger.

        Args:
            name: Logger name.
            log_dir: Directory to store JSONL event logs. Defaults to data/results/logs.
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Avoid adding handlers multiple times if re-initialized
        if not self.logger.handlers:
            # Console handler for standard output
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # Determine log directory for JSONL events
        if log_dir is None:
            # Default to project structure: data/results/logs
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.log_dir = base_dir / "data" / "results" / "logs"
        else:
            self.log_dir = log_dir

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.log_dir / "events.jsonl"

        # Ensure the file exists
        if not self.jsonl_path.exists():
            self.jsonl_path.touch()

    def _write_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Write a structured event to the JSONL file.

        Args:
            event_type: The type of event (e.g., DEGENERATE_DIALOGUE_TRUNCATED).
        """
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "logger": self.name,
            "data": data
        }
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def log_degenerate_dialogue_truncated(
        self,
        dialogue_id: str,
        original_length: int,
        truncated_length: int,
        ngram_overlap: float,
        reason: str = "N-gram overlap exceeded threshold"
    ) -> None:
        """
        Log a DEGENERATE_DIALOGUE_TRUNCATED event.

        This method specifically handles the edge case where a dialogue
        is truncated due to high n-gram overlap, writing the details
        to the JSONL event log.

        Args:
            dialogue_id: Unique identifier for the dialogue.
            original_length: Length of the dialogue before truncation.
            truncated_length: Length of the dialogue after truncation.
            ngram_overlap: The calculated n-gram overlap score.
            reason: Explanation for the truncation.
        """
        self.warning(
            f"DEGENERATE_DIALOGUE_TRUNCATED: Dialogue {dialogue_id} "
            f"truncated from {original_length} to {truncated_length} tokens "
            f"(overlap: {ngram_overlap:.4f})"
        )
        self._write_event(
            EVENT_DEGENERATE_DIALOGUE_TRUNCATED,
            {
                "dialogue_id": dialogue_id,
                "original_length": original_length,
                "truncated_length": truncated_length,
                "ngram_overlap": ngram_overlap,
                "reason": reason
            }
        )

    def log_training_oom(self, model_name: str, available_memory_gb: float) -> None:
        """Log a training OOM event."""
        self.error(f"TRAINING_OOM: Model {model_name} out of memory")
        self._write_event(
            EVENT_TRAINING_OOM,
            {
                "model_name": model_name,
                "available_memory_gb": available_memory_gb
            }
        )

    def log_data_download_success(self, dataset_name: str, path: str) -> None:
        """Log a successful data download."""
        self.info(f"DATA_DOWNLOAD_SUCCESS: {dataset_name} -> {path}")
        self._write_event(
            EVENT_DATA_DOWNLOAD_SUCCESS,
            {
                "dataset_name": dataset_name,
                "path": path
            }
        )

    def log_data_download_failure(self, dataset_name: str, error: str) -> None:
        """Log a failed data download."""
        self.error(f"DATA_DOWNLOAD_FAILURE: {dataset_name} - {error}")
        self._write_event(
            EVENT_DATA_DOWNLOAD_FAILURE,
            {
                "dataset_name": dataset_name,
                "error": error
            }
        )


# Global logger instance
_global_logger: Optional[SocraticLogger] = None


def get_logger(name: str = "socratic", log_dir: Optional[Path] = None) -> SocraticLogger:
    """
    Get or create a global logger instance.

    Args:
        name: Logger name (used for global caching).
        log_dir: Directory for JSONL logs.

    Returns:
        SocraticLogger instance.
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = SocraticLogger(name, log_dir)
    return _global_logger
