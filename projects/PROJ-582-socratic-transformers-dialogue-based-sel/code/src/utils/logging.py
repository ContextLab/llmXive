"""
Structured logging utility for the Socratic Transformers pipeline.

Handles specific edge-case events (e.g., DEGENERATE_DIALOGUE_TRUNCATED)
by writing structured JSON lines to disk, ensuring reproducibility and
easy downstream parsing for analysis.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the project root is in the path for imports if run as a script
# though typically this is handled by the runner environment.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class SocraticLogger:
    """
    A specialized logger that outputs structured JSON lines for specific
    research events, alongside standard logging for human readability.

    This satisfies the requirement to log `DEGENERATE_DIALOGUE_TRUNCATED`
    events as JSON lines for precise edge-case tracking.
    """

    DEGENERATE_DIALOGUE_TRUNCATED = "DEGENERATE_DIALOGUE_TRUNCATED"

    def __init__(
        self,
        name: str = "socratic_pipeline",
        log_dir: Optional[str] = None,
        level: int = logging.INFO,
    ):
        """
        Initialize the logger.

        Args:
            name: Name of the logger.
            log_dir: Directory to write JSONL logs. Defaults to `data/results/logs`.
            level: Logging level (e.g., logging.INFO).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers if re-initialized
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler for structured JSON logs
        self.log_dir = Path(log_dir) if log_dir else _PROJECT_ROOT / "data" / "results" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.json_log_path = self.log_dir / f"{name.lower()}_events.jsonl"
        self.file_handler = logging.FileHandler(self.json_log_path, mode="w")
        self.file_handler.setLevel(level)
        # We use a custom formatter or just write raw JSON via a custom handler
        # For this utility, we will expose a specific method to write JSON lines
        # to keep the structure strict, rather than relying on a formatter.
        # However, we keep the file handler open for potential text logs if needed.
        # For now, we focus on the JSONL method.

    def _write_json_line(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Writes a single JSON line to the structured log file.

        Args:
            event_type: The type of event (e.g., DEGENERATE_DIALOGUE_TRUNCATED).
        """
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data,
        }

        try:
            with open(self.json_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except IOError as e:
            self.logger.error(f"Failed to write JSON log: {e}")

    def log_degenerate_dialogue_truncation(
        self,
        dialogue_id: str,
        ngram_overlap: float,
        reason: str,
        original_length: int,
        truncated_length: int,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Logs a DEGENERATE_DIALOGUE_TRUNCATED event.

        This is the specific handler required by the Edge Case requirement.

        Args:
            dialogue_id: Unique identifier for the dialogue instance.
            ngram_overlap: The calculated n-gram overlap score (> 0.9).
        """
        if ngram_overlap <= 0.9:
            self.logger.warning(
                f"N-gram overlap {ngram_overlap} is not > 0.9. "
                "Logging DEGENERATE_DIALOGUE_TRUNCATED only for high overlap."
            )
            # Still log if explicitly requested, but warn.
            # The task implies this is the trigger condition.

        payload = {
            "dialogue_id": dialogue_id,
            "ngram_overlap": ngram_overlap,
            "reason": reason,
            "original_length": original_length,
            "truncated_length": truncated_length,
        }

        if extra_context:
            payload.update(extra_context)

        self._write_json_line(self.DEGENERATE_DIALOGUE_TRUNCATED, payload)

        # Also log a standard message for visibility
        self.logger.info(
            f"Event: {self.DEGENERATE_DIALOGUE_TRUNCATED} - "
            f"Dialogue {dialogue_id} truncated due to {reason} "
            f"(Overlap: {ngram_overlap:.4f})"
        )

    def log_generic_event(
        self, event_type: str, data: Dict[str, Any], level: int = logging.INFO
    ) -> None:
        """
        Logs a generic structured event.

        Args:
            event_type: Custom event type string.
        """
        self._write_json_line(event_type, data)
        self.logger.log(level, f"Event: {event_type} - {data}")


# Convenience function for quick script usage
def get_logger(name: str = "socratic_pipeline") -> SocraticLogger:
    """Returns a configured SocraticLogger instance."""
    return SocraticLogger(name=name)