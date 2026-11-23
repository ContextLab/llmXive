"""
Human Review Trigger Script (T013c)

This script acts as the automation wrapper for the human-in-the-loop review process.
It monitors for the exit condition of the Expert System Validator (T013) and
automatically invokes the Human Review Consumer (T013b) if the condition is met.

Trigger Conditions:
1. Exit code 42 from the preceding expert_system_validator.py run.
2. Presence of the 'needs_human_review.json' file in the data directory.

Workflow:
1. Check if 'needs_human_review.json' exists in the data/synthetic_benchmark directory.
2. If it exists, log the trigger event.
3. Invoke 'human_review_consumer.py' to process the review.
4. Propagate the exit code from the consumer script.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Import project utilities to ensure path consistency
from utils.config import get_project_root, get_data_dir


def check_trigger_conditions() -> tuple[bool, str]:
    """
    Checks if the conditions for triggering human review are met.

    Returns:
        tuple: (bool, str) - (is_triggered, reason)
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    benchmark_dir = data_dir / "synthetic_benchmark"
    needs_review_file = benchmark_dir / "needs_human_review.json"

    # Condition 1: Check for the presence of the needs_human_review.json file
    if needs_review_file.exists():
        try:
            with open(needs_review_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            if isinstance(content, list) and len(content) > 0:
                return True, f"Found {len(content)} items requiring human review in {needs_review_file.name}"
            elif isinstance(content, dict) and len(content) > 0:
                return True, f"Found {len(content)} keys in {needs_review_file.name} requiring review"
            else:
                # File exists but is empty or invalid structure
                return False, "needs_human_review.json exists but is empty or malformed"
        except (json.JSONDecodeError, IOError) as e:
            return False, f"Error reading {needs_review_file.name}: {str(e)}"
    
    return False, "No trigger conditions met (file not found or empty)"


def invoke_human_review_consumer() -> int:
    """
    Invokes the human_review_consumer.py script to process the review.

    Returns:
        int: The exit code of the consumer script.
    """
    project_root = get_project_root()
    consumer_script = project_root / "code" / "data_generation" / "human_review_consumer.py"

    if not consumer_script.exists():
        print(f"ERROR: Consumer script not found at {consumer_script}")
        return 1

    print(f"Invoking human review consumer: {consumer_script}")
    
    try:
        # Run the consumer script as a subprocess
        # We pass the current environment and inherit stdin/stdout for interactive CLI usage if needed
        result = subprocess.run(
            [sys.executable, str(consumer_script)],
            cwd=project_root,
            capture_output=False, # Allow direct output to see CLI progress
            text=True
        )
        
        return result.returncode
    
    except FileNotFoundError:
        print(f"ERROR: Python interpreter not found or script execution failed.")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to invoke consumer script: {str(e)}")
        return 1


def main():
    """
    Main entry point for the Human Review Trigger.
    """
    print(f"[{datetime.now().isoformat()}] Starting Human Review Trigger (T013c)...")
    
    is_triggered, reason = check_trigger_conditions()
    
    if is_triggered:
        print(f"[TRIGGER DETECTED] {reason}")
        print("Initiating human review workflow...")
        
        exit_code = invoke_human_review_consumer()
        
        if exit_code == 0:
            print(f"[SUCCESS] Human review workflow completed successfully.")
            return 0
        else:
            print(f"[WARNING] Human review workflow returned exit code: {exit_code}")
            return exit_code
    else:
        print(f"[SKIPPED] {reason}")
        print("No human review required at this time.")
        return 0


if __name__ == "__main__":
    sys.exit(main())