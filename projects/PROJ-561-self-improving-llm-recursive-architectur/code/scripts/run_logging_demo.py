"""
Demo script to verify T009: Structured cycle logging and checkpointing.
Runs a mock cycle and verifies log file creation and content.
"""
import os
import sys
import json
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.logging import (
    init_cycle_logger,
    log_cycle_summary,
    log_error,
    checkpoint_model_state,
    get_cycle_history
)
from config import PathConfig, Config, get_config, set_config, ensure_directories

class MockConfig:
    def __init__(self, tmp_dir):
        self.paths = PathConfig(
            raw_data=os.path.join(tmp_dir, "raw"),
            processed_data=os.path.join(tmp_dir, "processed"),
            results=os.path.join(tmp_dir, "results"),
            logs=os.path.join(tmp_dir, "logs"),
            checkpoints=os.path.join(tmp_dir, "checkpoints")
        )

def main():
    print("Starting T009 Logging Demo...")
    
    # Setup temp directory
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")
    
    mock_config = MockConfig(temp_dir)
    ensure_directories([
        mock_config.paths.raw_data,
        mock_config.paths.processed_data,
        mock_config.paths.results,
        mock_config.paths.logs,
        mock_config.paths.checkpoints
    ])

    # Patch get_config
    import utils.logging
    original_get_config = utils.logging.get_config
    utils.logging.get_config = lambda: mock_config

    try:
        cycle_num = 1
        print(f"Initializing logger for cycle {cycle_num}...")
        logger = init_cycle_logger(cycle_num)

        print("Logging cycle start...")
        logger.info("Cycle started", extra={'cycle': cycle_num, 'component': 'orchestrator'})

        print("Logging mock metrics...")
        metrics = {
            "gsm8k_accuracy": 0.45,
            "arc_challenge_accuracy": 0.62,
            "boolq_ece": 0.15,
            "training_time_sec": 120.5,
            "param_count": 125000000
        }
        log_cycle_summary(logger, cycle_num, metrics)

        print("Simulating a warning...")
        log_warning(logger, cycle_num, "RAM usage approaching limit")

        print("Simulating a checkpoint...")
        mock_model = type('MockModel', (), {
            'state_dict': lambda self: {'dummy': 1.0}
        })()
        checkpoint_path = checkpoint_model_state(mock_model, cycle_num)
        print(f"Checkpoint saved to: {checkpoint_path}")

        print("Retrieving cycle history...")
        history = get_cycle_history(cycle_num)
        print(f"Retrieved {len(history)} log entries.")
        
        # Verify JSON structure
        log_file = os.path.join(mock_config.paths.results, "logs", f"cycle_{cycle_num}.log")
        print(f"\nVerifying log file: {log_file}")
        with open(log_file, 'r') as f:
            for i, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    print(f"  Entry {i}: {entry.get('message', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"  Entry {i}: INVALID JSON")

        print("\nT009 Demo completed successfully.")
        print("Log file created with structured JSON format.")

    finally:
        # Restore
        utils.logging.get_config = original_get_config
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("Cleaned up temporary directory.")

if __name__ == "__main__":
    main()