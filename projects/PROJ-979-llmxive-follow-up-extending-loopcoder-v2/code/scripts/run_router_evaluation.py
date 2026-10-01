import os
import sys
import logging
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.router_evaluation import main as run_router_evaluation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting router evaluation script...")
    try:
        run_router_evaluation()
        logger.info("Router evaluation completed successfully.")
    except Exception as e:
        logger.error(f"Router evaluation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()