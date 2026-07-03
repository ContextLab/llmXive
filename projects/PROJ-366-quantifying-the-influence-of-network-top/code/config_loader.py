"""
Script to initialize and validate the configuration system.
Creates a default config.yaml if missing and validates paths.
"""
import os
import sys
import json
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, get_config, get_simulation_config, get_gnn_hyperparameters, get_paths

def main():
    """Initialize configuration and print summary."""
    print("Initializing configuration system...")
    
    # Initialize config (will create defaults if config.yaml missing)
    config = get_config()
    
    # Ensure directories exist
    paths = get_paths()
    for dir_name, dir_path in paths.items():
        if dir_name != "code_root" and dir_name != "contracts":
            full_path = Path(dir_path)
            if not full_path.exists():
                print(f"Creating directory: {full_path}")
                full_path.mkdir(parents=True, exist_ok=True)
    
    # Save default config if it was just created
    if not Path("config.yaml").exists():
        config.save("config.yaml")
        print("Created default config.yaml")
    
    # Print summary
    print("\n--- Configuration Summary ---")
    print(f"Config Path: {config._config_path}")
    print(f"Random Seed: {config.get('seeds.random_seed')}")
    print(f"Data Root: {paths['data_root']}")
    print(f"Simulation Cores: {get_simulation_config()['cores']}")
    print(f"GNN Layers: {get_gnn_hyperparameters()['num_layers']}")
    print(f"Bond Cutoff: {config.get('analysis.bond_cutoff')}")
    print("--------------------------------\n")
    
    # Validate critical paths
    print("Validating paths...")
    valid = True
    for dir_name, dir_path in paths.items():
        if dir_name == "code_root":
            continue
        p = Path(dir_path)
        if not p.exists():
            print(f"  [MISSING] {dir_path}")
            valid = False
        else:
            print(f"  [OK] {dir_path}")
    
    if valid:
        print("\nAll paths validated successfully.")
    else:
        print("\nWarning: Some paths were missing and may need manual creation.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
