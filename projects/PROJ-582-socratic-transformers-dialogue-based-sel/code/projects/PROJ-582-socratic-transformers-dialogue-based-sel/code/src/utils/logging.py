"""
Structured logging utility for Socratic Transformers project.

Handles degenerate dialogue events as JSON lines to support
the "negative selection on belief" mechanism and edge case analysis.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.config import get_config


class SocraticLogger:
    """
    A structured logger that writes events as JSON lines to a file
    and optionally to stdout/stderr.

    Designed to capture degenerate dialogue events (e.g., failed critiques,
    empty revisions, logical contradictions) for downstream statistical analysis.
    """

    def __init__(
        self,
        log_file: Optional[Path] = None,
        level: int = logging.INFO,
        include_timestamp: bool = True,
    ):
        """
        Initialize the SocraticLogger.

        Args:
            log_file: Path to the JSONL log file. If None, uses default from config.
            level: Logging level (e.g., logging.DEBUG, logging.INFO).
            include_timestamp: Whether to include ISO timestamp in each record.
        """
        self.level = level
        self.include_timestamp = include_timestamp

        # Determine log file path from config or argument
        if log_file is None:
            config = get_config()
            log_dir = Path(config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "socratic_events.jsonl"
        else:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

        self.log_file = log_file
        self.file_handler = logging.FileHandler(self.log_file)
        self.file_handler.setLevel(level)

        # Formatter for file handler (we handle JSON manually)
        self.file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Setup root logger for this module
        self.logger = logging.getLogger("socratic_logger")
        self.logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        self.logger.addHandler(self.file_handler)

        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)  # Only show warnings/errors on console
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger.addHandler(console_handler)

    def _build_record(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construct a structured log record.

        Args:
            event_type: Type of event (e.g., "degenerate_dialogue", "critique_failure").
            data: Additional event-specific data.

        Returns:
            Dictionary ready for JSON serialization.
        """
        record = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() if self.include_timestamp else None,
            "data": data,
        }
        return record

    def log_degenerate_event(
        self,
        event_type: str,
        question: Optional[str] = None,
        initial_answer: Optional[str] = None,
        critique: Optional[str] = None,
        revised_answer: Optional[str] = None,
        error_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a degenerate dialogue event as a JSON line.

        Degenerate events include:
        - Failed critique generation
        - Empty or invalid revised answers
        - Logical contradictions detected
        - Token overflow or timeout during generation

        Args:
            event_type: Specific type of degenerate event.
            question: The original question (if applicable).
            initial_answer: The model's initial answer (if applicable).
            critique: The generated critique (if applicable).
            revised_answer: The revised answer (if applicable).
            error_reason: Reason for degeneracy (e.g., "empty_critique").
            metadata: Additional context (e.g., model_id, seed, token_count).
        """
        data = {
            "question": question,
            "initial_answer": initial_answer,
            "critique": critique,
            "revised_answer": revised_answer,
            "error_reason": error_reason,
            "metadata": metadata or {},
        }

        record = self._build_record(event_type, data)
        json_line = json.dumps(record, ensure_ascii=False, default=str)

        # Write to file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json_line + "\n")

        # Log to internal logger (which writes to file again via handler, 
        # but we already wrote manually to ensure strict JSONL format)
        self.logger.log(self.level, json_line)

    def log_critique_failure(
        self,
        question: str,
        initial_answer: str,
        failure_mode: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Convenience method to log a specific critique failure.

        Args:
            question: The question being critiqued.
            initial_answer: The answer that failed critique.
            failure_mode: Type of failure (e.g., "no_critique_generated", "invalid_json").
            details: Additional failure details.
        """
        self.log_degenerate_event(
            event_type="critique_failure",
            question=question,
            initial_answer=initial_answer,
            error_reason=failure_mode,
            metadata=details or {},
        )

    def log_revision_failure(
        self,
        question: str,
        initial_answer: str,
        critique: str,
        failure_mode: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Convenience method to log a revision failure.

        Args:
            question: The original question.
            initial_answer: The original answer.
            critique: The critique that triggered revision.
            failure_mode: Type of failure (e.g., "no_revision", "circular_logic").
            details: Additional failure details.
        """
        self.log_degenerate_event(
            event_type="revision_failure",
            question=question,
            initial_answer=initial_answer,
            critique=critique,
            error_reason=failure_mode,
            metadata=details or {},
        )

    def log_dialogue_success(
        self,
        question: str,
        initial_answer: str,
        critique: str,
        revised_answer: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a successful dialogue tuple generation.

        Args:
            question: The original question.
            initial_answer: The initial answer.
            critique: The generated critique.
            revised_answer: The final revised answer.
            metadata: Additional context (e.g., token counts, timing).
        """
        data = {
            "question": question,
            "initial_answer": initial_answer,
            "critique": critique,
            "revised_answer": revised_answer,
        }
        record = self._build_record("dialogue_success", data)
        json_line = json.dumps(record, ensure_ascii=False, default=str)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json_line + "\n")

        self.logger.log(self.level, json_line)


def get_logger(log_file: Optional[Path] = None) -> SocraticLogger:
    """
    Factory function to get a SocraticLogger instance.

    Args:
        log_file: Optional custom log file path.

    Returns:
        Configured SocraticLogger instance.
    """
    return SocraticLogger(log_file=log_file)
