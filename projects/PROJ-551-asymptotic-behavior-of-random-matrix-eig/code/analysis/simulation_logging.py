import logging
from pathlib import Path
from utils.config import get_project_paths

def setup_simulation_logger():
    paths = get_project_paths()
    log_file = paths['logs'] / 'simulation_run.log'
    logger = logging.getLogger("simulation_run")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(sh)
    return logger

def log_simulation_start(params):
    logger = setup_simulation_logger()
    logger.info(f"Starting simulation with parameters: {params}")

def log_simulation_end(result):
    logger = setup_simulation_logger()
    logger.info(f"Simulation completed. Run ID: {result['run_id']}, Top Eigenvalue: {result['eigenvalues'][0]['value']}")
