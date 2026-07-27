"""
Visualization wrapper script for T049.
Executes the visualization logic.
"""
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from viz.plots import main as viz_main
from utils.logging import initialize_logging

def main():
    log_path = Path("data/processed/visualization.log")
    logger = initialize_logging(log_path=log_path, level=logging.INFO)
    logger.log("start_viz")
    try:
        viz_main()
        logger.log("end_viz", status="success")
    except Exception as e:
        logger.log("end_viz", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
