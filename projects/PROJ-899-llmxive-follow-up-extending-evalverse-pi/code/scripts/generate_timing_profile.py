import os
import sys
import logging
from pathlib import Path
from src.models.evaluate import generate_timing_profile
from src.utils import setup_logging

def main():
    """Script wrapper for T024 timing profile generation."""
    setup_logging()
    from src.models.evaluate import main as evaluate_main
    return evaluate_main()

if __name__ == "__main__":
    sys.exit(main())