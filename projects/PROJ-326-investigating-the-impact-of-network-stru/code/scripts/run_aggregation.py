import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.aggregate_results import main as aggregate_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="Run aggregation of analysis results.")
    parser.parse_args()
    
    setup_logging()
    return aggregate_main()

if __name__ == "__main__":
    sys.exit(main())