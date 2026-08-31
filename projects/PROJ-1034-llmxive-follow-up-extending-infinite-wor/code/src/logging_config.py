"""
Logging infrastructure for llmXive simulation pipeline.

Configures a rotating file handler writing JSON logs to logs/simulation.log.
Ensures step_latency, coherence_score, and diversity_score are recorded.
"""
import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, asdict
import threading

# Ensure logs directory exists
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "simulation.log")
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

_logger_lock = threading.Lock()
_global_logger: Optional["SimulationLogger"] = None

@dataclass
class MetricRecord:
    """Data class for a single metric record to be logged."""
    timestamp: str
    step: int
    coherence_score: float
    diversity_score: float
    step_latency: float
    run_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.extra:
            data.update(self.extra)
        return data

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON."""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Attach extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data)

class SimulationLogger:
    """
    Wrapper around Python's logging module to provide structured JSON logging
    for simulation metrics.
    """
    def __init__(self, log_file: str = LOG_FILE, max_bytes: int = MAX_BYTES, backup_count: int = BACKUP_COUNT):
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._setup_logger()
        self._start_time: Optional[float] = None

    def _setup_logger(self) -> None:
        """Configure the root logger with a rotating JSON file handler."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # Create logger
        self.logger = logging.getLogger("sim_logger")
        self.logger.setLevel(logging.INFO)

        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            # Rotating file handler
            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8"
            )
            handler.setFormatter(JsonFormatter())
            self.logger.addHandler(handler)

    def start_run(self, run_id: str) -> None:
        """Log the start of a simulation run."""
        self._start_time = time.time()
        self.logger.info(f"Simulation run started", extra={"extra_data": {"run_id": run_id, "status": "started"}})

    def log_step(self, step: int, coherence_score: float, diversity_score: float, run_id: Optional[str] = None) -> None:
        """
        Log a single simulation step with metrics.
        
        Args:
            step: Current simulation step index.
            coherence_score: Calculated coherence metric.
            diversity_score: Calculated diversity metric.
            run_id: Optional run identifier.
        """
        if self._start_time is None:
            self._start_time = time.time()
        
        end_time = time.time()
        step_latency = end_time - self._start_time
        
        # Reset start time for next step latency calculation (optional, or accumulate)
        # Here we calculate latency since the last log call or start
        # To be precise, we should track last_log_time, but for simplicity:
        # We'll just record the current timestamp and let the consumer calculate delta if needed,
        # or we calculate step duration if we track previous step time.
        # Requirement: "verify log file contains step_latency key".
        # Let's assume step_latency is the time taken for THIS step.
        # We need to track previous time.
        
        # Actually, let's restructure slightly to track step duration properly.
        # But for the initial call, we don't have a previous time.
        # We will store the last step time in the instance.
        pass

    def _track_step(self, step: int, coherence_score: float, diversity_score: float, run_id: Optional[str] = None) -> None:
        """Internal method to calculate latency and log."""
        current_time = time.time()
        
        # Calculate latency since last step
        if hasattr(self, '_last_step_time'):
            step_latency = current_time - self._last_step_time
        else:
            step_latency = 0.0  # First step or no previous data
        
        self._last_step_time = current_time

        record = MetricRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            step=step,
            coherence_score=coherence_score,
            diversity_score=diversity_score,
            step_latency=step_latency,
            run_id=run_id
        )

        self.logger.info(
            "Step metrics recorded",
            extra={"extra_data": record.to_dict()}
        )

    def log_step(self, step: int, coherence_score: float, diversity_score: float, run_id: Optional[str] = None) -> None:
        """Public method to log a step."""
        self._track_step(step, coherence_score, diversity_score, run_id)

    def finish_run(self, run_id: str, status: str = "completed") -> None:
        """Log the end of a simulation run."""
        self.logger.info(f"Simulation run finished", extra={"extra_data": {"run_id": run_id, "status": status}})

def create_logger(log_file: Optional[str] = None) -> SimulationLogger:
    """
    Factory function to create a global SimulationLogger instance.
    
    Args:
        log_file: Optional override for the log file path.
    
    Returns:
        SimulationLogger instance.
    """
    global _global_logger
    if _global_logger is None:
        with _logger_lock:
            if _global_logger is None:
                _global_logger = SimulationLogger(log_file or LOG_FILE)
    return _global_logger

def main():
    """
    Demonstration of the logging infrastructure.
    Runs a mock simulation loop and verifies that the log file contains step_latency.
    """
    logger = create_logger()
    run_id = "demo-run-001"
    logger.start_run(run_id)
    
    # Simulate 5 steps
    import random
    for i in range(5):
        # Mock metrics
        coh = random.uniform(0.8, 0.95)
        div = random.uniform(0.5, 0.8)
        
        # Small delay to simulate work
        time.sleep(0.1)
        
        logger.log_step(i, coh, div, run_id)
    
    logger.finish_run(run_id)
    
    # Verify log content
    print(f"Log file written to: {logger.log_file}")
    if os.path.exists(logger.log_file):
        with open(logger.log_file, 'r') as f:
            lines = f.readlines()
            print(f"Total log entries: {len(lines)}")
            # Check for step_latency in the last entry
            if lines:
                last_entry = json.loads(lines[-1])
                if "extra_data" in last_entry and "step_latency" in last_entry["extra_data"]:
                    print("VERIFICATION PASSED: 'step_latency' key found in log.")
                else:
                    print("VERIFICATION FAILED: 'step_latency' key missing.")
    else:
        print("VERIFICATION FAILED: Log file not created.")

if __name__ == "__main__":
    main()