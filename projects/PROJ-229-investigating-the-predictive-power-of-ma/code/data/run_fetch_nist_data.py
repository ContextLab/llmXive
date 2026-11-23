"""Run the NIST data fetch pipeline.

This script invokes the ``main`` function from ``code/data/fetch_nist_data.py``.
The ``main`` function is responsible for downloading the NIST dataset,
processing it, and writing the resulting JSON file to ``data/raw/nist_data.json``.
Running this script as ``python code/data/run_fetch_nist_data.py`` will
produce the required artifact.
"""

import logging
from data.fetch_nist_data import main as fetch_nist_main

# Configure a basic logger for the script execution.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def run():
    """Execute the NIST data fetch pipeline."""
    logger.info("Starting NIST data fetch...")
    try:
        fetch_nist_main()
    except Exception as exc:
        logger.exception("NIST data fetch failed: %s", exc)
        raise
    else:
        logger.info("NIST data fetch completed successfully.")

if __name__ == "__main__":
    run()