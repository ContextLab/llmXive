import sys
from pathlib import Path
from src.config import ensure_environment, get_config_summary
from src.data.config import is_data_directory_ready, get_data_summary

def main():
    """
    Main entry point for setting up the project environment.
    Ensures all required directories exist and the environment is configured.
    """
    print("=== llmXive Project Setup ===")
    
    # Ensure environment variables and configuration are ready
    ensure_environment()
    config_summary = get_config_summary()
    print(f"Project Root: {config_summary['project_root']}")
    print(f"Data Root: {config_summary['data_root']}")
    
    # Ensure data directories are ready
    is_ready = is_data_directory_ready()
    if is_ready:
        print("✓ All required data directories are ready.")
    else:
        print("✗ Data directory setup failed.")
        return 1
        
    data_summary = get_data_summary()
    print(f"Data directories: {list(data_summary.keys())}")
    
    print("=== Setup Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
