import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import numpy as np

from sim.health_monitor import HealthMonitor

@dataclass
class MetricRecord:
    """Structured record for a single simulation step."""
    timestamp: str
    step: int
    coherence_score: float
    diversity_score: float
    step_latency: float
    memory_mb: float
    is_valid: bool = True
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SimulationLogger:
    """
    Handles logging of simulation metrics to file.
    Integrates with HealthMonitor to detect NaNs and State Explosions.
    """
    def __init__(self, output_path: str, monitor: Optional[HealthMonitor] = None):
        self.output_path = output_path
        self.monitor = monitor or HealthMonitor()
        self.buffer: List[MetricRecord] = []
        self.flush_count = 0
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Initialize file if needed
        if not os.path.exists(output_path):
            with open(output_path, 'w') as f:
                pass  # Create empty file

    def log_step(self, step: int, metrics: Dict[str, Any], memory_mb: float, warnings: List[str] = None) -> bool:
        """
        Logs a single step.
        Returns True if the step is valid (no NaNs/Explosions), False otherwise.
        """
        timestamp = datetime.now().isoformat()
        
        # Extract known metrics with defaults
        coherence = metrics.get('coherence_score', 0.0)
        diversity = metrics.get('diversity_score', 0.0)
        latency = metrics.get('step_latency', 0.01)

        # Validate using HealthMonitor
        validation_report = self.monitor.validate_metrics_and_handle(
            metrics, step=step, memory_mb=memory_mb
        )

        is_valid = validation_report['valid']
        step_warnings = validation_report.get('nan_details', []) + [validation_report.get('explosion_details', '')]
        if warnings:
            step_warnings.extend(warnings)

        record = MetricRecord(
            timestamp=timestamp,
            step=step,
            coherence_score=coherence,
            diversity_score=diversity,
            step_latency=latency,
            memory_mb=memory_mb,
            is_valid=is_valid,
            warnings=step_warnings
        )

        self.buffer.append(record)
        return is_valid

    def flush(self):
        """Writes buffered records to disk."""
        if not self.buffer:
            return

        with open(self.output_path, 'a') as f:
            for record in self.buffer:
                # Ensure no NaNs are written to disk (replace with null or specific flag)
                # The task requires graceful handling, so we log the warning but still record the step
                # if it's flagged as invalid due to NaN, we might want to mark it specifically.
                # Here we write the raw float (which might be NaN string if json allows, or we sanitize)
                # We rely on the HealthMonitor to flag it.
                d = record.to_dict()
                # Sanitize NaN for JSON compatibility if necessary
                for key, val in d.items():
                    if isinstance(val, float):
                        if np.isnan(val):
                            d[key] = None
                        elif np.isinf(val):
                            d[key] = None
                f.write(json.dumps(d) + '\n')
        
        self.buffer.clear()
        self.flush_count += 1

    def close(self):
        self.flush()

def create_logger(output_path: str) -> SimulationLogger:
    """Factory to create a logger instance."""
    return SimulationLogger(output_path)

def main():
    """Test the logger and health monitor integration."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as tmp:
        path = tmp.name

    logger = create_logger(path)
    
    # Simulate a good step
    logger.log_step(0, {'coherence_score': 0.9, 'diversity_score': 0.5, 'step_latency': 0.01}, 100.0)
    
    # Simulate a step with NaN
    logger.log_step(1, {'coherence_score': float('nan'), 'diversity_score': 0.5, 'step_latency': 0.01}, 100.0)
    
    # Simulate a step with explosion
    logger.log_step(2, {'coherence_score': 1e15, 'diversity_score': 0.5, 'step_latency': 0.01}, 100.0)
    
    logger.close()
    
    # Verify file content
    with open(path, 'r') as f:
        print("Log contents:")
        print(f.read())
    
    os.unlink(path)

if __name__ == "__main__":
    main()