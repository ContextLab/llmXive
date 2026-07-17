#!/usr/bin/env python3
"""
Script to setup the project environment and create necessary directories.

This script ensures that all required data directories are created and
validates that the environment is properly configured for the llmXive
pipeline.
"""
import sys
from pathlib import Path

# Add code to path
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from src.config import ensure_environment, get_config_summary
from src.data.config import is_data_directory_ready, get_data_summary

def main():
    """Main entry point for environment setup."""
    print("Setting up llmXive environment...")
    print("-" * 50)
    
    # Ensure environment is configured
    if not ensure_environment():
        print("ERROR: Failed to configure environment.")
        sys.exit(1)
    
    print("✓ Environment configuration successful")
    
    # Verify data directories
    if not is_data_directory_ready():
        print("ERROR: Data directories are not ready.")
        sys.exit(1)
    
    print("✓ Data directories are ready")
    
    # Display configuration summary
    print("\nConfiguration Summary:")
    print("-" * 50)
    summary = get_config_summary()
    for key, value in summary.items():
        if key == "paths":
            print(f"{key}:")
            for path_key, path_value in value.items():
                print(f"  {path_key}: {path_value}")
        else:
            print(f"{key}: {value}")
    
    # Display data directory status
    print("\nData Directory Status:")
    print("-" * 50)
    data_summary = get_data_summary()
    for name, info in data_summary.items():
        status = "✓" if info["exists"] else "✗"
        print(f"{status} {name}: {info['path']}")
    
    print("\n" + "-" * 50)
    print("Environment setup complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())