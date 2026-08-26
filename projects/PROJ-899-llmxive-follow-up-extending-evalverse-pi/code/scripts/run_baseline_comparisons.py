import os
import sys
import logging
from pathlib import Path
from src.models.evaluate import main as evaluate_main
from src.utils import setup_logging

def main():
    """Wrapper to run T019 baseline comparisons."""
    logger = setup_logging("run_baseline_comparisons")
    logger.info("Running baseline comparisons (T019)...")
    evaluate_main()

if __name__ == "__main__":
    main()
