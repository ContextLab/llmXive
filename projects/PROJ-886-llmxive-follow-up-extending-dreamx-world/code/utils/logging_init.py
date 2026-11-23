"""
Logging initialization utility for DreamX-Lite project.
Specifically handles the logging of parameter count deltas during model initialization.
"""
import logging
import os
from pathlib import Path

def log_param_delta(param_delta: float, log_dir: str = "logs") -> None:
    """
    Logs the parameter count delta to logs/init.log.

    Args:
        param_delta: The difference in parameter count (Base - Lite).
                     Expected to be negative if Lite has fewer parameters.
        log_dir: Directory where the log file will be created.
    """
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file_path = os.path.join(log_dir, "init.log")

    # Configure logger specifically for this task
    # We use a separate logger to avoid interfering with other logging configurations
    logger = logging.getLogger("dreamx_init")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicates if called multiple times
    logger.handlers = []

    # Create file handler
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setLevel(logging.INFO)

    # Set format: only the message as per spec "Param Delta: -{value}"
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    # Format the message. The spec asks for "Param Delta: -{value}".
    # If param_delta is already negative (e.g. -5000), we output "Param Delta: --5000" or handle sign.
    # Usually "Delta" implies (New - Old). If Lite is smaller, Delta is negative.
    # The spec format "Param Delta: -{value}" suggests the value itself might be the magnitude,
    # or we just print the negative number. Let's assume the input is the signed difference.
    # To match "Param Delta: -X" where X is the reduction amount, we should print the absolute reduction.
    # However, if the input is simply the delta, we print it.
    # Let's interpret "Param Delta: -{value}" as the literal string format where {value} is the number.
    # If the delta is -1000, we write "Param Delta: -1000".
    # If the delta is 1000, we write "Param Delta: -1000" (which would be weird).
    # Given the context "parameter count decreases", the delta is likely negative.
    # We will format it as: f"Param Delta: {param_delta}"
    # But the spec says "Param Delta: -{value}". This implies the value is the magnitude of reduction.
    # Let's assume the caller passes the *reduction amount* (positive) or we calculate it.
    # To be safe and strictly follow the string pattern "Param Delta: -{value}":
    # If param_delta is the signed change (e.g. -500), we want "Param Delta: -500".
    # If the spec means "Delta: -(reduction)", and reduction is 500, then -500.
    # Let's just print the signed delta directly, assuming the caller provides the signed difference.
    # Actually, looking at T014: "parameter count decreases by the size...".
    # Let's assume the input `param_delta` is the signed difference (Lite - Base), which is negative.
    # The string "Param Delta: -{value}" might be a typo in the spec or implies printing the negative sign explicitly.
    # Let's output exactly "Param Delta: {param_delta}" if param_delta is negative, which looks like "Param Delta: -123".
    # If the spec literally wants the minus sign hardcoded: "Param Delta: -{abs(value)}".
    # Let's assume the standard interpretation: Log the delta.
    message = f"Param Delta: {param_delta}"
    logger.info(message)

def main() -> None:
    """
    Main entry point for testing the logging function.
    Simulates a parameter delta calculation and logs it.
    """
    # Example usage: Base model has 100M params, Lite has 95M. Delta = -5M.
    # We simulate a delta of -12345678 for demonstration.
    simulated_delta = -12345678.0
    log_param_delta(simulated_delta)
    print(f"Logged parameter delta: {simulated_delta} to logs/init.log")

if __name__ == "__main__":
    main()