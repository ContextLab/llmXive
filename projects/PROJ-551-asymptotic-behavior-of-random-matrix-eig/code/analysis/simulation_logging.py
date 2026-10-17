import logging
from datetime import datetime

logger = logging.getLogger("simulation")

def log_simulation_start(params: dict):
    logger.info(f"Simulation started at {datetime.now().isoformat()} with parameters: {params}")

def log_simulation_end(result: dict):
    logger.info(f"Simulation ended. Run ID: {result['run_id']}, Top Eigenvalue: {result['eigenvalues'][0]['value']}")
