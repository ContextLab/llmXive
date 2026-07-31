import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from code.config import get_config

class NumericalLogger:
    """
    Logs numerical residuals and convergence flags.
    Outputs JSON lines to data/metadata/residuals.json.
    """

    def __init__(self):
        self.log_file = Path(get_config().data_dir) / "residuals.json"
        logging.basicConfig(filename=str(self.log_file), level=logging.INFO, format='%(message)s')


    def log_residual(self, task: str, converged: bool, L: int, W: float, realization_index: int, residual_norm: float):
        """
        Logs the residual norm after eigenvalue decomposition.
        """
        log_entry = {
            "task": task,
            "L": L,
            "W": W,
            "realization_index": realization_index,
            "residual_norm": residual_norm,
            "converged": converged
        }

        with open(self.log_file, "a") as f:
            json.dump(log_entry, f)
            f.write('\n') # Ensure each entry is a separate JSON line

def get_logger():
    """
    Returns an instance of the NumericalLogger.
    """
    return NumericalLogger()