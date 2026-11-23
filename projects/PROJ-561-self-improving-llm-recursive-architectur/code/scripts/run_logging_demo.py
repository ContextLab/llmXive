"""
Demonstration script for T009: Structured cycle logging and checkpointing.

This script simulates a mock cycle to verify that:
1. A log file is created with structured JSON format.
2. Checkpoint files are written to disk.
3. Cycle history is populated in memory.
"""
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logging import (
    init_cycle_logger,
    log_cycle_summary,
    get_cycle_history,
    log_error,
    log_warning
)
from config import get_config, set_config, PathConfig, Hyperparameters, SafetyConstraints

def main():
    print("Starting T009 Logging Demo...")

    # Create a temporary directory for the demo to avoid cluttering the project
    demo_dir = tempfile.mkdtemp(prefix="t009_demo_")
    print(f"Using temporary directory: {demo_dir}")

    # Override config paths to point to the demo directory
    original_config = get_config()
    try:
        new_path_config = PathConfig(
            data_dir=os.path.join(demo_dir, "data"),
            results_dir=os.path.join(demo_dir, "results"),
            log_dir=os.path.join(demo_dir, "logs"),
            checkpoint_dir=os.path.join(demo_dir, "checkpoints"),
            template_dir=original_config.path_config.template_dir
        )
        new_config = original_config._replace(path_config=new_path_config)
        set_config(new_config)

        # Ensure directories exist
        os.makedirs(new_path_config.log_dir, exist_ok=True)
        os.makedirs(new_path_config.checkpoint_dir, exist_ok=True)

        cycle_number = 1

        # 1. Initialize logger
        logger = init_cycle_logger(cycle_number)
        print(f"Initialized logger for cycle {cycle_number}")

        # 2. Log some intermediate steps
        update_cycle_log(cycle_number, {"step": "loading_model", "status": "success"})
        update_cycle_log(cycle_number, {"step": "training_epoch", "epoch": 1, "loss": 2.5})
        update_cycle_log(cycle_number, {"step": "training_epoch", "epoch": 2, "loss": 1.8})

        # 3. Log a warning
        log_warning(cycle_number, "Memory usage approaching limit")

        # 4. Create a mock checkpoint (simulate model state)
        mock_model_state = {
            "layer_1.weight": [0.1, 0.2, 0.3],
            "layer_1.bias": [0.0],
            "metadata": {"version": "1.0"}
        }
        mock_optimizer_state = {
            "state": {},
            "param_groups": [{"lr": 5e-5}]
        }

        checkpoint_path = checkpoint_model_state(
            cycle_number,
            mock_model_state,
            mock_optimizer_state
        )
        print(f"Checkpoint saved to: {checkpoint_path}")

        # Verify checkpoint exists
        if os.path.exists(checkpoint_path):
            print("✓ Checkpoint file exists on disk.")
            # Try to read it back to verify content
            if checkpoint_path.endswith('.json'):
                with open(checkpoint_path, 'r') as f:
                    data = json.load(f)
                    assert "model_state" in data
                    assert data["cycle_number"] == cycle_number
                    print("✓ Checkpoint content is valid JSON with expected keys.")
            else:
                # Assume torch format, just check file size > 0
                size = os.path.getsize(checkpoint_path)
                assert size > 0
                print(f"✓ Checkpoint file size: {size} bytes.")

        # 5. Log final summary
        metrics = {
            "accuracy": 0.85,
            "loss": 1.2,
            "flops": 1000000
        }
        log_cycle_summary(cycle_number, metrics, status="completed")

        # 6. Verify log file exists and contains JSON
        log_path = os.path.join(new_path_config.log_dir, f"cycle_{cycle_number}_*.log")
        # Find the actual file
        log_files = [f for f in os.listdir(new_path_config.log_dir) if f.startswith(f"cycle_{cycle_number}_")]
        if not log_files:
            raise FileNotFoundError(f"No log file found for cycle {cycle_number} in {new_path_config.log_dir}")

        actual_log_path = os.path.join(new_path_config.log_dir, log_files[0])
        print(f"Log file created at: {actual_log_path}")

        with open(actual_log_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0, "Log file is empty"
            
            # Verify each line is valid JSON
            for i, line in enumerate(lines):
                try:
                    entry = json.loads(line.strip())
                    assert "timestamp" in entry
                    assert "cycle" in entry
                    assert "level" in entry
                except json.JSONDecodeError as e:
                    raise ValueError(f"Line {i+1} is not valid JSON: {e}")
            
            print("✓ Log file contains valid structured JSON entries.")

        # 7. Verify in-memory history
        history = get_cycle_history()
        assert len(history) == 1, f"Expected 1 history entry, got {len(history)}"
        assert history[0]["cycle_number"] == cycle_number
        assert history[0]["status"] == "completed"
        assert "accuracy" in history[0]["metrics"]
        print("✓ In-memory cycle history is correct.")

        print("\n✅ T009 Verification Successful: Log file created with structured JSON format.")

    finally:
        # Restore original config
        set_config(original_config)
        # Cleanup
        shutil.rmtree(demo_dir)
        print(f"Cleaned up temporary directory: {demo_dir}")

if __name__ == "__main__":
    main()
