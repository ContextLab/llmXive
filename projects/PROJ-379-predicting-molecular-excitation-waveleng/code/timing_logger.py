import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
WALL_CLOCK_BUDGET_SECONDS = 6 * 3600  # 6 hours in seconds (SC-002)
TIMING_OUTPUT_PATH = Path("data/processed/timing.json")

class PipelineTimer:
    """
    Measures and logs total wall-clock time of the pipeline (ingest to evaluate).
    Ensures compliance with SC-002 (≤6 hours) and raises a warning if exceeded.
    """

    def __init__(self, output_path: Optional[Path] = None):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.output_path = output_path or TIMING_OUTPUT_PATH
        self.metrics: Dict[str, Any] = {}

    def start(self) -> None:
        """Start the pipeline timer."""
        self.start_time = time.time()
        logger.info("Pipeline timing started.")

    def stop(self) -> None:
        """Stop the pipeline timer and record metrics."""
        if self.start_time is None:
            raise RuntimeError("Timer was not started. Call start() first.")
        
        self.end_time = time.time()
        elapsed_seconds = self.end_time - self.start_time
        
        self.metrics = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": elapsed_seconds,
            "elapsed_hours": elapsed_seconds / 3600.0,
            "budget_seconds": WALL_CLOCK_BUDGET_SECONDS,
            "budget_hours": WALL_CLOCK_BUDGET_SECONDS / 3600.0,
            "compliance_status": "PASS" if elapsed_seconds <= WALL_CLOCK_BUDGET_SECONDS else "FAIL"
        }

        # Log compliance check
        if elapsed_seconds > WALL_CLOCK_BUDGET_SECONDS:
            logger.warning(
                f"SC-002 COMPLIANCE FAILED: Pipeline took {elapsed_seconds:.2f} seconds "
                f"({elapsed_seconds/3600:.2f} hours), exceeding the 6-hour budget."
            )
        else:
            logger.info(
                f"SC-002 COMPLIANCE PASSED: Pipeline completed in {elapsed_seconds:.2f} seconds "
                f"({elapsed_seconds/3600:.2f} hours), within the 6-hour budget."
            )

    def save(self) -> None:
        """Save timing metrics to the output JSON file."""
        if not self.metrics:
            raise RuntimeError("No metrics to save. Ensure stop() has been called.")

        # Ensure the output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2)

        logger.info(f"Timing metrics saved to {self.output_path}")

    def get_metrics(self) -> Dict[str, Any]:
        """Return the current metrics dictionary."""
        return self.metrics


def main() -> None:
    """
    Main entry point for the timing logger.
    This script is designed to be imported and used by the pipeline orchestration,
    but can also be run standalone to demonstrate the timing logic.
    
    When run standalone, it simulates a pipeline execution to verify the logger works.
    """
    # Ensure data/processed directory exists for testing
    TIMING_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    timer = PipelineTimer()
    
    # Simulate a pipeline run (e.g., ingest -> train -> evaluate)
    # In a real scenario, the pipeline steps would be called between start() and stop()
    logger.info("Simulating pipeline steps...")
    timer.start()
    
    # Simulate work (e.g., data loading, training)
    # Using a small sleep to ensure the script runs quickly in tests but still measures time
    time.sleep(1.0) 
    
    timer.stop()
    timer.save()

    metrics = timer.get_metrics()
    print(f"Pipeline completed in {metrics['elapsed_seconds']:.2f} seconds.")
    print(f"Compliance Status: {metrics['compliance_status']}")


if __name__ == "__main__":
    main()