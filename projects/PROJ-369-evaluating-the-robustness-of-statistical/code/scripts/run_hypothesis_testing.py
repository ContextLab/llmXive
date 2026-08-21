import os
import sys
import json
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).resolve().parent
src_path = code_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.analysis.hypothesis_tests import main as hypothesis_main
from src.utils.logging import setup_logger, log_info, log_error

def main():
    logger = setup_logger()
    log_info("Starting Hypothesis Testing Stage...")

    try:
        hypothesis_main()
        log_info("Hypothesis Testing stage completed successfully.")
    except Exception as e:
        log_error(f"Hypothesis Testing stage failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
