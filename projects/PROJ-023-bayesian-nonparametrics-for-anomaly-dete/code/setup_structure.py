"""
Project Structure Setup Script

This script creates the required directory structure for the Bayesian Nonparametrics
for Anomaly Detection project as specified in tasks.md.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    root = Path(__file__).parent.parent

    # Define required directories relative to project root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "paper",
        "paper/figures",
        "contracts",
        "tests",
        "tests/contract",
        "tests/integration",
        "code/lib",
        "code/scripts",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path.relative_to(root)}")

    print(f"\nSetup complete. Created {created_count} new directories.")

    # Verify structure
    print("\nVerifying directory structure:")
    for dir_path in directories:
        full_path = root / dir_path
        if full_path.exists():
            print(f"  ✓ {full_path.relative_to(root)}")
        else:
            print(f"  ✗ {full_path.relative_to(root)} (MISSING)")

    return 0

if __name__ == "__main__":
    exit(main())