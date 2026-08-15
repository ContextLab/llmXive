import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from router_evaluation import main as run_router_evaluation

def main():
    """Main entry point for the router evaluation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Running router evaluation...")
    
    try:
        run_router_evaluation()
        logger.info("Router evaluation completed successfully.")
    except Exception as e:
        logger.error(f"Router evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()