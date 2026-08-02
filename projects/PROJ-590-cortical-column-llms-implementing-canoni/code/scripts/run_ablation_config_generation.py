import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.experiments.ablation import main as generate_configs_main

if __name__ == "__main__":
    print("Running ablation config generation (Task T025a)...")
    generate_configs_main()
    print("Done.")
