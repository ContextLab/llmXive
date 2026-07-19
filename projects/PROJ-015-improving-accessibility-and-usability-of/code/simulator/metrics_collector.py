import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from utils.logger import get_logger

logger = get_logger(__name__)

class MetricsCollector:
    """
    Collects usability metrics including completion time, error count,
    and explanation engagement time.
    """

    def __init__(self):
        self.session_start_time: Optional[float] = None
        self.session_end_time: Optional[float] = None
        self.error_count: int = 0
        self.explanation_engagement_start: Optional[float] = None
        self.explanation_engagement_total: float = 0.0
        self.metrics: Dict[str, Any] = {}

    def start_session(self) -> None:
        """Record the start time of the interaction session."""
        self.session_start_time = time.time()
        logger.info("Session started.")

    def stop_session(self) -> None:
        """Record the end time of the interaction session."""
        self.session_end_time = time.time()
        logger.info("Session ended.")

    def record_error(self) -> None:
        """Increment the error count."""
        self.error_count += 1
        logger.debug("Error recorded. Total errors: %d", self.error_count)

    def start_explanation_engagement(self) -> None:
        """Start tracking time spent engaging with an explanation."""
        if self.explanation_engagement_start is not None:
            logger.warning("Explanation engagement already in progress. Stopping previous timer.")
            self._stop_explanation_engagement()
        self.explanation_engagement_start = time.time()
        logger.debug("Explanation engagement started.")

    def stop_explanation_engagement(self) -> None:
        """Stop tracking time spent engaging with an explanation."""
        self._stop_explanation_engagement()
        logger.debug("Explanation engagement stopped.")

    def _stop_explanation_engagement(self) -> None:
        """Internal helper to stop the timer and accumulate duration."""
        if self.explanation_engagement_start is not None:
            end_time = time.time()
            duration = end_time - self.explanation_engagement_start
            self.explanation_engagement_total += duration
            self.explanation_engagement_start = None
            logger.debug("Accumulated engagement duration: %.3f seconds", duration)

    def finalize_metrics(self) -> Dict[str, Any]:
        """
        Calculate and return the final metrics dictionary.
        Includes completion_time_seconds, error_count, and explanation_engagement_time_seconds.
        """
        if self.session_start_time is None or self.session_end_time is None:
            raise RuntimeError("Session start or end time not recorded.")

        completion_time = self.session_end_time - self.session_start_time

        self.metrics = {
            "completion_time_seconds": completion_time,
            "error_count": self.error_count,
            "explanation_engagement_time_seconds": self.explanation_engagement_total
        }

        logger.info("Metrics finalized: %s", str(self.metrics))
        return self.metrics

    def reset(self) -> None:
        """Reset all metrics for a new session."""
        self.session_start_time = None
        self.session_end_time = None
        self.error_count = 0
        self.explanation_engagement_start = None
        self.explanation_engagement_total = 0.0
        self.metrics = {}
        logger.info("MetricsCollector reset.")

def main():
    """
    CLI entry point for testing the MetricsCollector.
    Simulates a session to ensure 'explanation_engagement_time_seconds' is calculated correctly.
    """
    collector = MetricsCollector()
    collector.start_session()
    
    # Simulate some work
    time.sleep(0.1) 
    collector.record_error()
    
    # Simulate explanation engagement
    collector.start_explanation_engagement()
    time.sleep(0.2)
    collector.stop_explanation_engagement()
    
    collector.stop_session()
    
    results = collector.finalize_metrics()
    print("Final Metrics:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    
    # Verify the specific field required by T016b
    assert "explanation_engagement_time_seconds" in results, "explanation_engagement_time_seconds missing!"
    assert isinstance(results["explanation_engagement_time_seconds"], float), "explanation_engagement_time_seconds must be float!"
    
    print("SUCCESS: explanation_engagement_time_seconds is correctly logged.")

if __name__ == "__main__":
    main()
