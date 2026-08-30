import sys
import logging
from pathlib import Path
from verify_moral_machine_source import main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Running verify_moral_machine_source.py")
    try:
        main()
        logger.info("verify_moral_machine_source.py completed successfully")
    except Exception as e:
        logger.error(f"verify_moral_machine_source.py failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
