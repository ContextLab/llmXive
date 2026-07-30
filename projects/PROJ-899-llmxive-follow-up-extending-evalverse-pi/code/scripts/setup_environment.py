"""
Script to initialize the project environment and data directory structure.
Creates raw, processed, state, cache, figures, and reports directories.
Validates the environment setup.
"""
import sys
from pathlib import Path

from src.config import ensure_environment, get_config_summary
from src.data.config import is_data_directory_ready, get_data_summary


def main() -> int:
    """
    Main entry point for environment setup.
    Returns 0 on success, 1 on failure.
    """
    print("Initializing llmXive environment...")

    # Ensure project-level environment (config files, etc.)
    print("Ensuring project environment...")
    ensure_environment()

    # Ensure data directories exist
    print("Ensuring data directory structure...")
    from src.data.config import ensure_directories
    dirs = ensure_directories()

    print("\nDirectory Structure Created:")
    for name, path in dirs.items():
        print(f"  - {name}: {path}")

    # Validate readiness
    print("\nValidating data directory readiness...")
    if not is_data_directory_ready():
        print("ERROR: Data directories are not ready or writable.")
        return 1

    print("Environment setup successful.")
    print("\nConfiguration Summary:")
    summary = get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\nData Summary:")
    data_summary = get_data_summary()
    for key, value in data_summary.items():
        status = "OK" if value.get("exists") else "MISSING"
        print(f"  {key}: {status}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
