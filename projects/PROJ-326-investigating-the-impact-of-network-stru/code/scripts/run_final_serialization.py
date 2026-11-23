"""
Wrapper script to invoke the final serialization logic (T037d).
Ensures the run-book can execute the serialization step.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.analysis.serialize_final import main as serialize_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="Run final serialization (T037d)")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting final serialization...")

    # Mock sys.argv to pass args to the underlying main
    sys.argv = [
        "run_final_serialization.py",
        "--config", args.config,
        "--output", args.output
    ]
    
    try:
        serialize_main()
        logger.info("Final serialization completed successfully.")
    except Exception as e:
        logger.error(f"Final serialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
