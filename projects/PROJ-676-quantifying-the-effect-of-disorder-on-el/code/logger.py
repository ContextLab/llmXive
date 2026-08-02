import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import logging

DATA_METADATA = Path("data/metadata")
DATA_METADATA.mkdir(parents=True, exist_ok=True)

class NumericalLogger:
    def __init__(self, output_path: Optional[Path] = None):
        self.output_path = output_path or DATA_METADATA / "residuals.json"
        self.entries = []
        self.logger = logging.getLogger("NumericalLogger")

    def log_residual(self, norm: float, flag: bool):
        entry = {
            "type": "residual",
            "norm": norm,
            "flag": flag,
            "timestamp": str(datetime.now())
        }
        self.entries.append(entry)
        self.logger.debug(f"Logged residual: norm={norm}, flag={flag}")

    def log_convergence(self, metric: float):
        entry = {
            "type": "convergence",
            "metric": metric,
            "timestamp": str(datetime.now())
        }
        self.entries.append(entry)
        self.logger.debug(f"Logged convergence: metric={metric}")

    def save(self):
        with open(self.output_path, 'w') as f:
            json.dump(self.entries, f, indent=2)
        self.logger.info(f"Saved {len(self.entries)} entries to {self.output_path}")

def get_logger(output_path: Optional[Path] = None) -> NumericalLogger:
    return NumericalLogger(output_path)

def log_residual_decorator(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            result = func(*args, **kwargs)
            logger.log_residual(norm=0.0, flag=True)
            return result
        except Exception as e:
            logger.log_residual(norm=float(e), flag=False)
            raise
    return wrapper

def log_convergence_decorator(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            result = func(*args, **kwargs)
            logger.log_convergence(metric=1.0)
            return result
        except Exception as e:
            logger.log_convergence(metric=0.0)
            raise
    return wrapper

def inject_log_residual(logger_instance: NumericalLogger, func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger_instance.log_residual(norm=0.0, flag=True)
            return result
        except Exception as e:
            logger_instance.log_residual(norm=float(e), flag=False)
            raise
    return wrapper

def inject_log_convergence(logger_instance: NumericalLogger, func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger_instance.log_convergence(metric=1.0)
            return result
        except Exception as e:
            logger_instance.log_convergence(metric=0.0)
            raise
    return wrapper
