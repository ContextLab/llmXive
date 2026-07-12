"""
Project Setup Script for llmXive: Video2GUI Follow-up
Creates the required directory structure as per the implementation plan.

Creates:
  - code/
  - data/raw/
  - data/benchmarks/
  - data/results/
  - tests/
"""
import os
import sys

def create_directories():
    """Create the project directory structure."""
    # Define relative paths based on the task requirements
    base_paths = [
        "code",
        "data/raw",
        "data/benchmarks",
        "data/results",
        "tests"
    ]

    created_count = 0
    existing_count = 0

    for path in base_paths:
        try:
            if os.path.exists(path):
                existing_count += 1
                print(f"[SKIP] Directory exists: {path}")
            else:
                os.makedirs(path, exist_ok=True)
                created_count += 1
                print(f"[CREATE] Directory created: {path}")
        except OSError as e:
            print(f"[ERROR] Failed to create {path}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"\nSetup complete. Created {created_count} directories, skipped {existing_count}.")

if __name__ == "__main__":
    create_directories()