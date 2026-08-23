import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.ablation import main as generate_configs_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Entry point for running ablation config generation."""
    logger.info("Starting ablation config generation script.")
    generate_configs_main()
    logger.info("Ablation config generation completed.")

if __name__ == "__main__":
    main()
