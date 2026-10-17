import logging
from pathlib import Path
from typing import Any, Dict
from utils.config import get_project_paths

def _get_logger():
    paths = get_project_paths()
    log_file = paths["logs"] / "simulation_run.log"
    
    logger = logging.getLogger("simulation_run")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def log_simulation_start(params: Dict[str, Any]):
    logger = _get_logger()
    logger.info(f"SIMULATION START: params={params}")

def log_simulation_end(result: Dict[str, Any]):
    logger = _get_logger()
    logger.info(f"SIMULATION END: run_id={result.get('run_id')}, top_eig={result.get('eigenvalues', [{}])[0].get('value') if result.get('eigenvalues') else 'N/A'}")
