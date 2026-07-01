import logging
import os
from pathlib import Path

def setup_logging():
    """
    Configure logging to write to data/ingest.log.
    Returns the root logger.
    """
    base_dir = Path(__file__).parent.parent
    log_file = base_dir / "data" / "ingest.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure basic logging
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # Also print to console for immediate feedback
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    logging.getLogger('').addHandler(console)

    return logging.getLogger(__name__)

def test_log_entry():
    """Write a test entry to verify logging works."""
    logger = setup_logging()
    logger.info("Logging configuration test successful.")