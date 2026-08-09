"""
Test script to verify logging infrastructure (T005).
Runs a few sample log events and ensures logs are written to logs/pipeline.log
in JSON format.
"""
import json
import os
from pathlib import Path
from code.utils.logging_config import setup_logging, get_logger, log_event

def main():
    # Setup logging
    logger = setup_logging(level="DEBUG", console_output=True)

    # Log a startup event
    log_event(
        logger,
        "INFO",
        "Pipeline started",
        task_id="T005",
        component="logging_test"
    )

    # Log a sample processing event
    log_event(
        logger,
        "DEBUG",
        "Simulating data processing step",
        participant_id="001",
        status="running",
        metrics={"nodes": 90, "edges": 4500}
    )

    # Log a warning
    log_event(
        logger,
        "WARNING",
        "Sample warning: Motion threshold exceeded",
        participant_id="002",
        fd_value=0.65
    )

    # Log an error simulation
    try:
        raise ValueError("Simulated error for logging test")
    except ValueError:
        log_event(
            logger,
            "ERROR",
            "Simulated error caught and logged",
            context="test_run"
        )

    # Log completion
    log_event(
        logger,
        "INFO",
        "Logging infrastructure test completed successfully",
        status="success"
    )

    # Verify log file exists and is valid JSON
    log_path = Path("logs/pipeline.log")
    if not log_path.exists():
        print("ERROR: Log file was not created.")
        return 1

    print(f"Log file created at: {log_path.absolute()}")

    # Validate JSON lines
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        valid_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if "timestamp" in entry and "level" in entry and "message" in entry:
                    valid_count += 1
                else:
                    print(f"Line {i+1}: Missing required JSON keys.")
            except json.JSONDecodeError as e:
                print(f"Line {i+1}: Invalid JSON - {e}")
                return 1

    print(f"Validated {valid_count} JSON log entries.")
    if valid_count > 0:
        print("T005 Logging infrastructure: PASSED")
        return 0
    else:
        print("T005 Logging infrastructure: FAILED (no valid entries)")
        return 1

if __name__ == "__main__":
    exit(main())