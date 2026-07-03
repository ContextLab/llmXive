"""
Script to generate checksums for data directories.

Usage:
    python scripts/generate_checksums.py
    python scripts/generate_checksums.py --verify
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.checksums import generate_checksums_for_directories, verify_all_checksums


def main():
    """Generate checksums for all data directories."""
    print("=== Generating Data Checksums ===\n")

    results = generate_checksums_for_directories()

    if not results:
        print("No data directories found or they are empty.")
        return 1

    print("\nGenerated checksum files:")
    for dir_name, file_path in results.items():
        print(f"  - {dir_name}: {file_path}")

    # Optionally verify
    print("\n=== Verifying Generated Checksums ===")
    success = verify_all_checksums()

    if success:
        print("\n✓ All checksums generated and verified successfully.")
        return 0
    else:
        print("\n✗ Some checksums failed verification!")
        return 1


if __name__ == "__main__":
    sys.exit(main())