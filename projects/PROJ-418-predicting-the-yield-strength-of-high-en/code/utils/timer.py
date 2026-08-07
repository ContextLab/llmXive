"""
Runtime monitoring utilities for the HEA yield strength prediction pipeline.

This module provides per-phase execution time tracking with warnings for
phases exceeding predefined thresholds, while maintaining the hard abort
enforcement at the end of the pipeline (enforced by T064).
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from datetime import datetime

from utils.logging import get_logger

# Constants for phase duration thresholds (in seconds)
# These are warnings thresholds; the hard abort is still enforced by T064 (2 hours total)
PHASE_THRESHOLDS = {
    "download": 300,          # 5 minutes
    "preprocess": 300,        # 5 minutes
    "descriptors": 600,       # 10 minutes
    "model_training": 3600,   # 1 hour
    "evaluation": 1800,       # 30 minutes
    "validation": 1800,       # 30 minutes
    "report_generation": 300, # 5 minutes
}

# Suggested parameter reductions for long-running phases
PARAMETER_SUGGESTIONS = {
    "model_training": "Reduce n_estimators or use fewer CV folds",
    "evaluation": "Reduce n_permutations or use fewer bootstrap resamples",
    "descriptors": "Review elemental property data for missing values causing retries",
}

logger = get_logger(__name__)

class PhaseTimer:
    """Context manager and tracker for per-phase execution times."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.phase_times: Dict[str, float] = {}
        self.phase_warnings: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.current_phase: Optional[str] = None
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def start_phase(self, phase_name: str) -> None:
        """Start timing a specific phase."""
        if self.current_phase is not None:
            logger.warning(f"Phase '{self.current_phase}' was not stopped before starting '{phase_name}'. Stopping previous phase.")
            self.stop_phase()
        
        self.current_phase = phase_name
        self.start_time = time.time()
        logger.info(f"Starting phase: {phase_name}")
    
    def stop_phase(self) -> float:
        """Stop timing the current phase and record the duration."""
        if self.current_phase is None:
            logger.warning("No active phase to stop.")
            return 0.0
        
        if self.start_time is None:
            logger.warning(f"Phase '{self.current_phase}' has no start time recorded.")
            return 0.0
        
        duration = time.time() - self.start_time
        self.phase_times[self.current_phase] = duration
        
        # Check against threshold
        threshold = PHASE_THRESHOLDS.get(self.current_phase)
        if threshold and duration > threshold:
            warning_msg = (
                f"Phase '{self.current_phase}' took {duration:.2f}s, "
                f"exceeding threshold of {threshold}s. "
                f"Suggestion: {PARAMETER_SUGGESTIONS.get(self.current_phase, 'Consider optimizing this phase.')}"
            )
            logger.warning(warning_msg)
            self.phase_warnings.append({
                "phase": self.current_phase,
                "duration_seconds": duration,
                "threshold_seconds": threshold,
                "suggestion": PARAMETER_SUGGESTIONS.get(self.current_phase, "Consider optimizing this phase.")
            })
        
        logger.info(f"Completed phase: {self.current_phase} in {duration:.2f}s")
        self.current_phase = None
        self.start_time = None
        return duration
    
    @contextmanager
    def timing_phase(self, phase_name: str):
        """Context manager for timing a phase."""
        self.start_phase(phase_name)
        try:
            yield
        finally:
            self.stop_phase()
    
    def save_runtime_report(self) -> None:
        """Save the runtime report to a JSON file."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase_times": self.phase_times,
            "warnings": self.phase_warnings,
            "total_runtime_seconds": sum(self.phase_times.values()),
            "hard_abort_threshold_seconds": 7200,  # 2 hours as per T064
            "status": "completed_with_warnings" if self.phase_warnings else "completed"
        }
        
        output_path = self.output_dir / "phase_runtime_report.json"
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Phase runtime report saved to {output_path}")
        
        # Return the report for potential programmatic use
        return report

# Global timer instance for convenience
_global_timer: Optional[PhaseTimer] = None

def get_timer() -> PhaseTimer:
    """Get or create the global timer instance."""
    global _global_timer
    if _global_timer is None:
        _global_timer = PhaseTimer()
    return _global_timer

def start_phase(phase_name: str) -> None:
    """Start timing a specific phase using the global timer."""
    get_timer().start_phase(phase_name)

def stop_phase() -> float:
    """Stop timing the current phase using the global timer."""
    return get_timer().stop_phase()

@contextmanager
def timing_phase(phase_name: str):
    """Context manager for timing a phase using the global timer."""
    with get_timer().timing_phase(phase_name):
        yield

def save_runtime_report() -> Dict[str, Any]:
    """Save the runtime report using the global timer."""
    return get_timer().save_runtime_report()

def main() -> None:
    """
    Demonstration of the timer functionality.
    This function is for testing purposes and should not be part of the main pipeline.
    """
    logger.info("Testing PhaseTimer functionality...")
    
    timer = PhaseTimer(output_dir="output")
    
    # Simulate various phases
    with timer.timing_phase("download"):
        time.sleep(0.5)
    
    with timer.timing_phase("model_training"):
        time.sleep(1.0)  # Simulate long-running phase
    
    with timer.timing_phase("evaluation"):
        time.sleep(0.3)
    
    # Save the report
    report = timer.save_runtime_report()
    logger.info(f"Runtime report: {json.dumps(report, indent=2)}")

if __name__ == "__main__":
    main()