"""
Script to generate ablation configuration files.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.experiments.ablation import main as generate_configs_main

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    generate_configs_main()

if __name__ == "__main__":
    main()
