"""
CLI script to execute the T016 task: Save processed graph with clusters and coefficients.
"""
import logging
import sys
from src.services.save_graph import main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

if __name__ == "__main__":
    setup_logging()
    main()
