"""
Script to setup the project environment.
"""
import sys
from pathlib import Path
from src.config import ensure_environment, get_config_summary
from src.data.config import is_data_directory_ready, get_data_summary

def main():
    """Main entry point for environment setup."""
    print("Setting up llmXive environment...")
    
    # Ensure directories
    ensure_environment()
    
    # Check data directory
    if is_data_directory_ready():
        print("✓ Data directory structure is ready.")
    else:
        print("✗ Data directory structure is not ready.")
    
    # Print configuration summary
    config = get_config_summary()
    data_summary = get_data_summary()
    
    print("\n=== Configuration Summary ===")
    for key, value in config.items():
        print(f"{key}: {value}")
    
    print("\n=== Data Directory Summary ===")
    for key, value in data_summary.items():
        print(f"{key}: {value}")
    
    print("\nEnvironment setup complete.")

if __name__ == "__main__":
    main()
