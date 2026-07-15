"""
Structured JSON logging utilities for the llmXive pipeline.

Provides a custom JSON formatter and helper functions to log prompts, seeds,
raw outputs, and evaluation results in a consistent, parseable format.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as JSON.

    Includes timestamp, level, logger name, message, and any extra fields
    passed in the log record.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in {"name", "msg", "args", "created", "filename",
                               "funcName", "levelname", "levelno", "lineno",
                               "module", "msecs", "pathname", "process",
                               "processName", "relativeCreated", "stack_info",
                               "exc_info", "exc_text", "thread", "threadName",
                               "message"}:
                    # Attempt to serialize, skip if not serializable
                    try:
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)

        return json.dumps(log_data)


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Creates and configures a logger with JSON formatting.

    Args:
        name: The name of the logger.
        log_file: Optional path to a log file. If provided, logs are written to
                  both the file and stdout. If None, logs go to stdout only.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = JsonFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_prompt(logger: logging.Logger, prompt_id: str, prompt_text: str,
               seed: int, condition: str, model: str = "CodeLlama-7B") -> None:
    """
    Logs a prompt request with its associated metadata.

    Args:
        logger: The logger instance.
        prompt_id: Unique identifier for the prompt instance.
        prompt_text: The actual prompt text sent to the model.
        seed: The random seed used for generation.
        condition: The prompt condition (e.g., 'zero_shot_basic').
        model: The model identifier used.
    """
    extra = {
        "event_type": "prompt",
        "prompt_id": prompt_id,
        "condition": condition,
        "seed": seed,
        "model": model,
        "prompt_text": prompt_text
    }
    logger.info(f"Prompt sent: {prompt_id}", extra=extra)


def log_raw_output(logger: logging.Logger, prompt_id: str, raw_output: str,
                   seed: int, condition: str, success: bool = True) -> None:
    """
    Logs the raw output from the LLM.

    Args:
        logger: The logger instance.
        prompt_id: The ID of the prompt that generated this output.
        raw_output: The raw text output from the model.
        seed: The seed used for generation.
        condition: The prompt condition.
        success: Whether the output was considered a valid code generation.
    """
    extra = {
        "event_type": "raw_output",
        "prompt_id": prompt_id,
        "condition": condition,
        "seed": seed,
        "success": success,
        "output_length": len(raw_output),
        "raw_output": raw_output
    }
    status = "success" if success else "failed"
    logger.info(f"Raw output received for {prompt_id} ({status})", extra=extra)


def log_evaluation_result(logger: logging.Logger, prompt_id: str,
                          correctness: bool, complexity: float,
                          condition: str) -> None:
    """
    Logs the results of an evaluation (correctness, quality metrics).

    Args:
        logger: The logger instance.
        prompt_id: The ID of the prompt being evaluated.
        correctness: Whether the generated code passed functional tests.
        complexity: The cyclomatic complexity score.
        condition: The prompt condition.
    """
    extra = {
        "event_type": "evaluation",
        "prompt_id": prompt_id,
        "condition": condition,
        "correctness": correctness,
        "complexity": complexity
    }
    logger.info(f"Evaluation result for {prompt_id}", extra=extra)


def main() -> None:
    """
    Simple test runner to demonstrate the logging utilities.
    """
    logger = get_logger("test_logging", "data/evaluation/test_log.jsonl")

    log_prompt(logger, "test-001", "Translate this Python code to JavaScript.", 42, "zero_shot_basic")
    log_raw_output(logger, "test-001", "function translate() { ... }", 42, "zero_shot_basic", success=True)
    log_evaluation_result(logger, "test-001", True, 3.5, "zero_shot_basic")

    print("Logging test completed. Check data/evaluation/test_log.jsonl")


if __name__ == "__main__":
    main()