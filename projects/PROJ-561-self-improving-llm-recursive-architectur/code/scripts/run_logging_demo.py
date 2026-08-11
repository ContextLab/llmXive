"""
Demonstration script for T009: Structured cycle logging.

This script simulates a mock cycle and writes structured JSON logs
to verify the logging functionality works as expected.

Usage:
    python scripts/run_logging_demo.py

Output:
    - results/logs/cycle_1.log (structured JSON log file)
    - Console output confirming log creation
"""

import os
import sys
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logging import (
    init_cycle_logger,
    update_cycle_log,
    checkpoint_model_state,
    log_cycle_summary,
    get_cycle_history,
    log_error
)
from config import get_config


def main():
    """Run a mock cycle and generate structured logs."""
    print("Starting mock cycle logging demonstration...")

    # Initialize logger for cycle 1
    cycle_number = 1
    logger = init_cycle_logger(cycle_number)
    print(f"Initialized logger for cycle {cycle_number}")

    # Simulate cycle events
    update_cycle_log(cycle_number, "CYCLE_START", {"timestamp": "2026-01-01T00:00:00Z"}, logger)
    print("Logged CYCLE_START")

    update_cycle_log(cycle_number, "MODEL_LOAD", {"model_name": "gpt-124m", "param_count": 124000000}, logger)
    print("Logged MODEL_LOAD")

    update_cycle_log(cycle_number, "TRAINING_START", {"epochs": 1, "batch_size": 4}, logger)
    print("Logged TRAINING_START")

    # Simulate a training step
    update_cycle_log(cycle_number, "TRAINING_STEP", {"epoch": 1, "loss": 2.45}, logger)
    print("Logged TRAINING_STEP")

    # Simulate evaluation
    update_cycle_log(cycle_number, "EVALUATION", {"GSM8K": 0.12, "ARC": 0.35, "BoolQ": 0.68}, logger)
    print("Logged EVALUATION")

    # Simulate checkpoint
    mock_state = {
        "weights": {"dummy": "state"},
        "cycle": cycle_number,
        "param_count": 124000000,
        "modification": {"type": "layer_add", "magnitude": 1}
    }
    checkpoint_path = checkpoint_model_state(cycle_number, mock_state)
    print(f"Checkpoint saved to: {checkpoint_path}")

    # Log cycle summary
    summary = {
        "status": "completed",
        "duration_seconds": 120.5,
        "final_loss": 2.15,
        "improvement": True,
        "metrics": {
            "GSM8K": 0.12,
            "ARC": 0.35,
            "BoolQ": 0.68
        }
    }
    log_cycle_summary(cycle_number, summary, logger)
    print("Logged CYCLE_SUMMARY")

    # Simulate an error (optional, for testing error logging)
    # log_error(cycle_number, "Simulated timeout", "TimeoutError", logger)

    # Verify log file
    log_path = os.path.join(project_root, "results", "logs", f"cycle_{cycle_number}.log")
    if os.path.exists(log_path):
        print(f"\n✓ Log file created successfully at: {log_path}")
        history = get_cycle_history(cycle_number)
        print(f"✓ Total log entries: {len(history)}")

        # Print first entry as sample
        if history:
            print("\nSample log entry:")
            print(json.dumps(history[0], indent=2))
    else:
        print(f"✗ Log file NOT found at: {log_path}")
        sys.exit(1)

    print("\nMock cycle logging demonstration completed successfully.")


if __name__ == "__main__":
    main()