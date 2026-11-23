"""
Logging configuration for simulation.
Replaces the fabricated metric generation with real logging infrastructure.
"""
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from logging.handlers import RotatingFileHandler

class MetricRecord:
    """Data class for simulation metrics."""
    def __init__(self, step: int, coherence: float, diversity: float, latency_ms: float):
        self.step = step
        self.coherence = coherence
        self.diversity = diversity
        self.latency_ms = latency_ms
        self.timestamp = datetime.now().isoformat()

class SimulationLogger:
    """
    Logger that writes JSON logs to a rotating file.
    Ensures step_latency is logged as required by T010.
    """
    def __init__(self, log_dir: str, filename: str = "simulation.log"):
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, filename)
        
        self.logger = logging.getLogger("SimulationLogger")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Rotating file handler
        handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Also log to console for debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

    def log_step_latency(self, step: int, latency_ms: float) -> None:
        """Log step latency as required by T010."""
        record = {
            "step": step,
            "step_latency": latency_ms,
            "timestamp": datetime.now().isoformat()
        }
        # Log as JSON string to ensure parseability
        self.logger.info(json.dumps(record))

    def log_metric(self, metric: MetricRecord) -> None:
        """Log a full metric record."""
        record = {
            "step": metric.step,
            "coherence": metric.coherence,
            "diversity": metric.diversity,
            "latency_ms": metric.latency_ms,
            "timestamp": metric.timestamp
        }
        self.logger.info(json.dumps(record))

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

def create_logger(config: Dict[str, Any]) -> SimulationLogger:
    """Factory function to create a logger based on config."""
    log_dir = config.get('output', {}).get('raw_data_dir', 'logs')
    filename = config.get('logging', {}).get('filename', 'simulation.log')
    return SimulationLogger(log_dir, filename)

def main():
    """Entry point for testing logging config."""
    config = {
        "output": {"raw_data_dir": "logs"},
        "logging": {"filename": "simulation.log"}
    }
    logger = create_logger(config)
    logger.info("Logger initialized successfully.")
    logger.log_step_latency(1, 15.5)
    logger.log_step_latency(2, 16.2)
    print("Logging test completed.")

if __name__ == "__main__":
    main()
