import logging
from datetime import datetime
from pathlib import Path
from llmxive_toolkit import paths

def log_simulation_start(params):
    logger = logging.getLogger("simulation_run")
    log_file = paths.data("logs", "simulation_run.log")
    # Ensure we use a file handler for the specific simulation log
    fh = logging.FileHandler(log_file)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    logger.info(f"Starting simulation with parameters: {params}")

def log_simulation_end(result):
    logger = logging.getLogger("simulation_run")
    logger.info(f"Simulation completed. Run ID: {result['run_id']}, Top Eigenvalue: {result['eigenvalues'][0].value if result['eigenvalues'] else 'N/A'}")
