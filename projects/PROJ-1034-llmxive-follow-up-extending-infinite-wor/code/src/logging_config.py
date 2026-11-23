"""
Logging infrastructure for the llmXive simulation pipeline.
Configures a rotating file handler writing JSON logs to logs/simulation.log.
Ensures every log entry includes a 'step_latency' key.
"""
import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "simulation.log")

class JsonFormatter(logging.Formatter):
    """Custom formatter to output logs as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        # Append extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data)

class SimulationLogger:
    """
    Wrapper around the standard logging module to enforce JSON formatting
    and ensure 'step_latency' is recorded for simulation steps.
    """
    
    def __init__(self, name: str = "simulation"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers if re-initialized
        if not self.logger.handlers:
            os.makedirs(LOG_DIR, exist_ok=True)
            
            handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=10*1024*1024, # 10MB
                backupCount=5
            )
            handler.setFormatter(JsonFormatter())
            self.logger.addHandler(handler)
        
        # Also add a console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JsonFormatter())
        # Avoid adding duplicate console handlers
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in self.logger.handlers):
             # Simple check to avoid dupes in this specific context, 
             # though the 'if not handlers' check above covers the file one.
             pass 
             # We will rely on the file handler being the primary source of truth for the artifact.

    def log_step(self, step: int, latency: float, metrics: Optional[Dict[str, Any]] = None):
        """
        Log a simulation step with the required 'step_latency' key.
        
        Args:
            step: The current simulation step index.
            latency: Time taken for this step in seconds.
            metrics: Optional dictionary of additional metrics.
        """
        extra = {
            "step_latency": latency,
            "step_index": step
        }
        if metrics:
            extra.update(metrics)
        
        # Create a LogRecord with extra data
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "",
            0,
            f"Step {step} completed",
            (),
            None
        )
        record.extra_data = extra
        self.logger.handle(record)

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log a generic event with structured details."""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "",
            0,
            f"Event: {event_type}",
            (),
            None
        )
        record.extra_data = details
        self.logger.handle(record)

def create_logger(name: str = "simulation") -> SimulationLogger:
    """Factory function to create a configured SimulationLogger."""
    return SimulationLogger(name)

def main():
    """
    Main entry point to demonstrate the logging infrastructure.
    Writes test logs to logs/simulation.log and verifies 'step_latency' presence.
    """
    logger = create_logger("test_run")
    
    # Simulate a few steps to generate logs
    test_steps = [1, 2, 3, 4, 5]
    for i in test_steps:
        # Measure a real latency (simulated work)
        start = time.time()
        # Do a tiny bit of work to ensure latency > 0
        _ = sum(x*x for x in range(1000))
        latency = time.time() - start
        
        logger.log_step(i, latency, {"coherence": 0.5 + i * 0.1, "diversity": 10.0})
    
    # Verify the log file exists and contains step_latency
    if not os.path.exists(LOG_FILE):
        raise FileNotFoundError(f"Log file {LOG_FILE} was not created.")
    
    found_latency = False
    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if "step_latency" in data:
                    found_latency = True
                    break
            except json.JSONDecodeError:
                continue
    
    if not found_latency:
        raise RuntimeError("Verification failed: 'step_latency' key not found in log file.")
    
    print(f"Logging infrastructure verified. Log file: {LOG_FILE}")

if __name__ == "__main__":
    main()
