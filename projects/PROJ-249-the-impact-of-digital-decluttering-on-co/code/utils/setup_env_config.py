"""
Utility script to initialize the environment configuration.
Creates necessary directories and saves the default configuration.
"""
import os
from pathlib import Path
from code.config.env_config import get_config, save_config, setup_data_directories

def main():
    """
    Initialize the project configuration and create required directories.
    """
    print("Initializing project environment configuration...")
    
    # Get configuration (this will create defaults or load from env)
    config = get_config()
    
    # Create all required directories
    directories = [
        config.data_raw,
        config.data_processed,
        config.data_compliance,
        config.results_dir,
        config.figures_dir,
        config.config_file.parent,
        config.seed_file.parent
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  Created/Verified: {directory}")
    
    # Save the configuration to disk
    save_config(config)
    print(f"\nConfiguration saved to: {config.config_file}")
    
    print("\nEnvironment configuration setup complete.")
    print(f"Project root: {config.project_root}")
    print(f"Data directories: raw, processed, compliance")
    print(f"Results directories: results, figures")

if __name__ == "__main__":
    main()