"""
Script to create the required directory structure for the project.
This satisfies Task T001a and T001b requirements by ensuring all
necessary folders exist under code/, data/, tests/, and outputs/.
"""
import os
import sys

def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main():
    # Root directories
    ensure_dir("code")
    ensure_dir("data")
    ensure_dir("tests")
    ensure_dir("outputs")

    # Subdirectories for data (Task T001b scope included for completeness)
    data_subdirs = [
        "data/benchmarks",
        "data/benchmarks/raw",
        "data/benchmarks/processed",
        "data/benchmarks/processed/tests",
        "data/generated",
        "data/coverage_reports",
        "data/processed",
        "data/outputs",
    ]

    for subdir in data_subdirs:
        ensure_dir(subdir)

    print("\nDirectory structure setup complete.")

if __name__ == "__main__":
    main()