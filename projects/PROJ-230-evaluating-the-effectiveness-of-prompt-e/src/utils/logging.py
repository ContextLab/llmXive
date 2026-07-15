import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the src directory is in the path if running as a script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Constants
LOG_DIR = Path("state/logs")
PROMPT_LOG_FILE = "prompts.jsonl"
RAW_OUTPUT_LOG_FILE = "raw_outputs.jsonl"
EVALUATION_LOG_FILE = "evaluations.jsonl"

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def _ensure_log_dirs() -> None:
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger that writes to both console (JSON) and a file (JSONL).

    Args:
        name: The name of the logger.
        log_file: Optional specific file name to write to. If None, defaults based on name/context.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    _ensure_log_dirs()

    # Console Handler (JSON formatted)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    # File Handler (JSONL formatted)
    if log_file:
        file_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(file_path, mode='a')
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger

def log_prompt(
    logger: logging.Logger,
    prompt_id: str,
    condition: str,
    seed: int,
    prompt_text: str,
    model_version: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a prompt interaction to the structured log.

    Args:
        logger: The logger instance to use.
        prompt_id: Unique identifier for this prompt instance.
        condition: The prompt condition (e.g., 'zero_shot_basic').
        seed: The random seed used.
        prompt_text: The actual text sent to the model.
        model_version: The version of the model used.
        metadata: Optional dictionary of additional metadata.
    """
    extra_data = {
        "event_type": "prompt",
        "prompt_id": prompt_id,
        "condition": condition,
        "seed": seed,
        "model_version": model_version,
        "prompt_length": len(prompt_text),
    }
    if metadata:
        extra_data.update(metadata)

    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"Prompt logged: {prompt_id}",
        args=(),
        exc_info=None
    )
    record.extra_data = extra_data
    logger.handle(record)

def log_raw_output(
    logger: logging.Logger,
    prompt_id: str,
    raw_output: str,
    status: str = "success",
    error_message: Optional[str] = None,
    latency_ms: Optional[float] = None
) -> None:
    """
    Log the raw output from an LLM call.

    Args:
        logger: The logger instance to use.
        prompt_id: The ID of the prompt that generated this output.
        raw_output: The raw text output from the model.
        status: 'success', 'failed', or 'timeout'.
        error_message: Error message if status is not success.
        latency_ms: Time taken for the request in milliseconds.
    """
    extra_data = {
        "event_type": "raw_output",
        "prompt_id": prompt_id,
        "status": status,
        "output_length": len(raw_output),
        "latency_ms": latency_ms,
    }
    if error_message:
        extra_data["error"] = error_message

    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO if status == "success" else logging.ERROR,
        pathname="",
        lineno=0,
        msg=f"Raw output logged for {prompt_id}",
        args=(),
        exc_info=None
    )
    record.extra_data = extra_data
    logger.handle(record)

def log_evaluation_result(
    logger: logging.Logger,
    translation_id: str,
    prompt_id: str,
    is_correct: bool,
    complexity_score: float,
    loc: int,
    condition: str
) -> None:
    """
    Log the result of an evaluation (correctness and quality metrics).

    Args:
        logger: The logger instance to use.
        translation_id: Unique ID for the translation.
        prompt_id: The ID of the prompt used.
        is_correct: Boolean indicating if the translation passed tests.
        complexity_score: Cyclomatic complexity score.
        loc: Lines of code in the translation.
        condition: The prompt condition used.
    """
    extra_data = {
        "event_type": "evaluation",
        "translation_id": translation_id,
        "prompt_id": prompt_id,
        "condition": condition,
        "is_correct": is_correct,
        "complexity_score": complexity_score,
        "loc": loc,
    }

    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"Evaluation result logged for {translation_id}",
        args=(),
        exc_info=None
    )
    record.extra_data = extra_data
    logger.handle(record)

def main() -> None:
    """
    Main entry point for testing the logging utility.
    Demonstrates logging a prompt, a raw output, and an evaluation result.
    """
    logger = get_logger("test_logger", log_file="test_session.jsonl")

    # Simulate a prompt log
    log_prompt(
        logger=logger,
        prompt_id="test-001",
        condition="zero_shot_basic",
        seed=42,
        prompt_text="Convert this Python function to JavaScript: def add(a, b): return a + b",
        model_version="codellama-7b",
        metadata={"source_file": "test.py"}
    )

    # Simulate a raw output log
    log_raw_output(
        logger=logger,
        prompt_id="test-001",
        raw_output="function add(a, b) { return a + b; }",
        status="success",
        latency_ms=150.5
    )

    # Simulate an evaluation result log
    log_evaluation_result(
        logger=logger,
        translation_id="trans-001",
        prompt_id="test-001",
        is_correct=True,
        complexity_score=1.0,
        loc=1,
        condition="zero_shot_basic"
    )

    print("Logging test completed. Check state/logs/test_session.jsonl for output.")

if __name__ == "__main__":
    main()
