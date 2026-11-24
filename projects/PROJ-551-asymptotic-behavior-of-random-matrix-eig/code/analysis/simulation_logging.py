import logging

logger = logging.getLogger("simulation_logging")

def log_simulation_start(params: dict) -> None:
    logger.info(f"Simulation starting with parameters: {params}")

def log_simulation_end(result: dict) -> None:
    logger.info(f"Simulation completed. Run ID: {result['run_id']}, Top Eigenvalue: {result['eigenvalues'][0]['value']:.6f}")
