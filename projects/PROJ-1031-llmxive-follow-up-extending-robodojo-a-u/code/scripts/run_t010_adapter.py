import os
import sys
import logging
import torch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from controller_adapter import run_adapter_pipeline, ValidationFailedError

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting T010 Adapter Pipeline Script")
    
    try:
        run_adapter_pipeline()
        logging.info("T010 completed successfully.")
    except ValidationFailedError as e:
        logging.error(f"Validation Failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
