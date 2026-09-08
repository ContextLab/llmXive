"""
Script to execute the materials data fetching pipeline.

This script invokes the `main` function from `code/data/fetch_materials.py`,
which handles downloading the Materials Project dataset (or falling back
to the MatBench dataset) and writes the resulting JSON to
`data/raw/materials_project_data.json`.

Running this script directly will produce the required artifact for
task T005a.
"""

import logging
from data.fetch_materials import main as fetch_materials_main

# Ensure the logger is configured (the fetch module uses the shared pipeline logger)
try:
    # The logger setup is performed inside the fetch module when needed,
    # but we call get_pipeline_logger to guarantee initialization.
    from utils.logger import get_pipeline_logger
    get_pipeline_logger()
except Exception:
    # If logger setup fails, fall back to basic config to avoid crashes.
    logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # Execute the fetch pipeline. Any exceptions will propagate,
    # causing the script to fail loudly as required.
    fetch_materials_main()
