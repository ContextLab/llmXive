"""
Logging configuration module for the research pipeline.

This module sets up a centralized logging infrastructure with a custom
adapter for derivation logging, ensuring that all data transformation
steps are recorded with appropriate context and severity levels.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json


class DerivationAdapter(logging.LoggerAdapter):
    """
    A custom logger adapter for derivation-specific logging.

    This adapter enriches log messages with metadata about the derivation
    process, such as the transformation type, parameters used, and output
    artifact paths.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Process the log message to include derivation context.

        Args:
            msg: The original log message.
            kwargs: Keyword arguments passed to the logger.

        Returns:
            A tuple containing the processed message and updated kwargs.
        """
        extra = self.extra or {}
        derivation_context = extra.get("derivation_context", {})

        # Prepend context to the message
        context_str = json.dumps(derivation_context, sort_keys=True)
        return f"[DERIVATION:{context_str}] {msg}", kwargs


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    enable_console: bool = True
) -> None:
    """
    Configure the root logger for the application.

    Sets up handlers for console and optional file output, configures
    the log format, and sets the global log level.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If provided, logs are
                  written to this file.
        enable_console: If True, logs are also printed to the console.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Define format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_derivation_logger(
    name: str,
    derivation_context: Optional[Dict[str, Any]] = None
) -> DerivationAdapter:
    """
    Get a derivation-specific logger adapter.

    Args:
        name: The name of the logger (typically the module name).
        derivation_context: A dictionary of context information to include
                            in all log messages from this adapter.

    Returns:
        A DerivationAdapter instance configured with the given context.
    """
    logger = logging.getLogger(name)
    return DerivationAdapter(logger, {"derivation_context": derivation_context or {}})


def log_derivation_params(
    logger: DerivationAdapter,
    params: Dict[str, Any],
    operation: str
) -> None:
    """
    Log the parameters of a derivation operation.

    Args:
        logger: The derivation logger adapter to use.
        params: A dictionary of parameters used in the derivation.
        operation: The name of the operation being performed.
    """
    logger.info(f"Starting derivation operation: {operation}", extra={"derivation_context": {"operation": operation, "params": params}})
    logger.debug(f"Derivation parameters: {json.dumps(params, indent=2)}")
