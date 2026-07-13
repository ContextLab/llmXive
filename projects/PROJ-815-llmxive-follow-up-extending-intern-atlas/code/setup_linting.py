"""
Setup script to initialize linting and formatting configurations.
This script ensures .ruff.toml and .black.toml are present in the code directory.
"""
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruff_config_path = os.path.join(base_dir, ".ruff.toml")
    black_config_path = os.path.join(base_dir, ".black.toml")

    # Verify ruff config
    if not os.path.exists(ruff_config_path):
        print(f"Error: {ruff_config_path} not found.")
        return 1
    
    # Verify black config
    if not os.path.exists(black_config_path):
        print(f"Error: {black_config_path} not found.")
        return 1

    print("Linting and formatting configurations are present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
