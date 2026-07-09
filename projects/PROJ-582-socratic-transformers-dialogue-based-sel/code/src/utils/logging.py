"""
Structured logging utility for Socratic Transformers project.

Handles specific edge case events such as DEGENERATE_DIALOGUE_TRUNCATED
by logging them as JSON lines for downstream analysis.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Constants for event types
EVENT_DEGENERATE_DIALOGUE_TRUNCATED = "DEGENERATE_DIALOGUE_TRUNCATED"
EVENT_DIALOGUE_GENERATION = "DIALOGUE_GENERATION"
EVENT_CRITIQUE_GENERATION = "CRITIQUE_GENERATION"
EVENT_REVISION_GENERATION = "REVISION_GENERATION"

class SocraticLogger:
    """
    A structured logger that outputs JSON lines for specific events
    and standard logs for general messages.
    """

    def __init__(self, log_dir: Optional[Path] = None, level: int = logging.INFO):
        """
        Initialize the logger.

        Args:
            log_dir: Directory to store JSON log files. Defaults to data/results/logs.
            level: Logging level.
        """
        self.level = level
        self.log_dir = log_dir or Path("data/results/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup standard logging for console output
        self.logger = logging.getLogger("socratic")
        self.logger.setLevel(level)

        # Prevent duplicate handlers if re-initialized
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Setup file handler for JSON lines
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_log_path = self.log_dir / f"events_{timestamp}.jsonl"
        self.json_file_handler = open(json_log_path, "a", encoding="utf-8")

    def _write_json_line(self, event_type: str, data: Dict[str, Any]) -> None:
        """Write a structured JSON line to the log file."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.json_file_handler.write(json.dumps(record) + "\n")
        self.json_file_handler.flush()

    def log_degenerate_dialogue_truncated(
        self,
        question_id: str,
        original_turns: int,
        truncated_turns: int,
        ngram_overlap: float,
        reason: str = "High n-gram overlap detected"
    ) -> None:
        """
        Log a DEGENERATE_DIALOGUE_TRUNCATED event.

        This is triggered when the dialogue generation loop detects
        excessive repetition (n-gram overlap > 0.9), indicating the
        model is stuck in a degenerate loop.

        Args:
            question_id: Unique identifier for the source question.
            original_turns: Number of turns before truncation.
            truncated_turns: Number of turns kept.
            ngram_overlap: The calculated overlap score that triggered truncation.
            reason: Human-readable reason for the truncation.
        """
        self.logger.warning(
            f"DEGENERATE_DIALOGUE_TRUNCATED: Question {question_id} "
            f"(overlap={ngram_overlap:.4f})"
        )

        event_data = {
            "question_id": question_id,
            "original_turns": original_turns,
            "truncated_turns": truncated_turns,
            "ngram_overlap": ngram_overlap,
            "reason": reason,
            "action_taken": "truncated"
        }

        self._write_json_line(EVENT_DEGENERATE_DIALOGUE_TRUNCATED, event_data)

    def log_dialogue_generation(
        self,
        question_id: str,
        total_turns: int,
        status: str = "success"
    ) -> None:
        """Log a standard dialogue generation event."""
        self.logger.info(f"Dialogue generated for {question_id}: {total_turns} turns")
        self._write_json_line(EVENT_DIALOGUE_GENERATION, {
            "question_id": question_id,
            "total_turns": total_turns,
            "status": status
        })

    def log_critique_generation(
        self,
        question_id: str,
        confidence_score: float,
        has_reasoning: bool
    ) -> None:
        """Log a critique generation event."""
        self.logger.info(f"Critique generated for {question_id} (confidence: {confidence_score})")
        self._write_json_line(EVENT_CRITIQUE_GENERATION, {
            "question_id": question_id,
            "confidence_score": confidence_score,
            "has_reasoning": has_reasoning
        })

    def log_revision_generation(
        self,
        question_id: str,
        revision_count: int
    ) -> None:
        """Log a revision generation event."""
        self.logger.info(f"Revision generated for {question_id}: {revision_count} attempts")
        self._write_json_line(EVENT_REVISION_GENERATION, {
            "question_id": question_id,
            "revision_count": revision_count
        })

    def close(self) -> None:
        """Close the JSON log file."""
        if self.json_file_handler:
            self.json_file_handler.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global logger instance for convenience
_global_logger: Optional[SocraticLogger] = None

def get_logger(log_dir: Optional[Path] = None, level: int = logging.INFO) -> SocraticLogger:
    """
    Get or create a global logger instance.

    Args:
        log_dir: Optional directory override.
        level: Logging level.

    Returns:
        A SocraticLogger instance.
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = SocraticLogger(log_dir=log_dir, level=level)
    return _global_logger