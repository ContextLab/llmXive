"""
Pipeline Timing Instrumentation Module (T032).

Implements instrumentation to log start/end timestamps for the entire
research pipeline execution to data/results/timing_report.json.

This module provides:
- Context manager for timing code blocks
- Functions to log pipeline stages
- Final report generation with aggregated timing data
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
OUTPUT_DIR = "data/results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "timing_report.json")

def ensure_output_dir():
    """Ensure the output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

class TimingTracker:
    """
    Tracks timing for pipeline stages.
    
    This class maintains a dictionary of timing events and provides
    methods to start, stop, and report timings.
    """
    
    def __init__(self):
        self.events: Dict[str, Dict[str, Any]] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.pipeline_start: Optional[float] = None
        self.pipeline_end: Optional[float] = None
    
    def start_pipeline(self):
        """Mark the start of the entire pipeline execution."""
        self.pipeline_start = time.time()
        self.start_time = self.pipeline_start
        logger.info(f"Pipeline started at {datetime.fromtimestamp(self.pipeline_start).isoformat()}")
    
    def end_pipeline(self):
        """Mark the end of the entire pipeline execution."""
        self.pipeline_end = time.time()
        self.end_time = self.pipeline_end
        logger.info(f"Pipeline ended at {datetime.fromtimestamp(self.pipeline_end).isoformat()}")
    
    def start_stage(self, stage_name: str):
        """Start timing a specific pipeline stage."""
        if stage_name in self.events:
            logger.warning(f"Stage {stage_name} already exists, overwriting")
        
        self.events[stage_name] = {
            "start_time": time.time(),
            "start_timestamp": datetime.fromtimestamp(time.time()).isoformat(),
            "duration_seconds": None,
            "end_timestamp": None
        }
        logger.info(f"Stage '{stage_name}' started")
    
    def end_stage(self, stage_name: str):
        """End timing a specific pipeline stage."""
        if stage_name not in self.events:
            logger.warning(f"Stage '{stage_name}' not found, cannot end timing")
            return
        
        end_time = time.time()
        start_time = self.events[stage_name]["start_time"]
        duration = end_time - start_time
        
        self.events[stage_name]["end_time"] = end_time
        self.events[stage_name]["end_timestamp"] = datetime.fromtimestamp(end_time).isoformat()
        self.events[stage_name]["duration_seconds"] = round(duration, 3)
        
        logger.info(f"Stage '{stage_name}' completed in {duration:.3f} seconds")
    
    @contextmanager
    def timed_stage(self, stage_name: str):
        """Context manager for timing a pipeline stage."""
        self.start_stage(stage_name)
        try:
            yield
        finally:
            self.end_stage(stage_name)
    
    def get_report(self) -> Dict[str, Any]:
        """Generate the final timing report."""
        if self.pipeline_start is None or self.pipeline_end is None:
            raise ValueError("Pipeline start/end times not set. Call start_pipeline() and end_pipeline().")
        
        total_duration = self.pipeline_end - self.pipeline_start
        
        report = {
            "pipeline_start": datetime.fromtimestamp(self.pipeline_start).isoformat(),
            "pipeline_end": datetime.fromtimestamp(self.pipeline_end).isoformat(),
            "total_duration_seconds": round(total_duration, 3),
            "stages": self.events,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_stages": len(self.events)
            }
        }
        
        # Add stage summary
        if self.events:
            stage_durations = [e["duration_seconds"] for e in self.events.values() if e["duration_seconds"] is not None]
            if stage_durations:
                report["stage_summary"] = {
                    "min_duration": min(stage_durations),
                    "max_duration": max(stage_durations),
                    "avg_duration": sum(stage_durations) / len(stage_durations),
                    "total_stage_time": sum(stage_durations)
                }
        
        return report
    
    def save_report(self, output_path: Optional[str] = None):
        """Save the timing report to a JSON file."""
        if output_path is None:
            output_path = OUTPUT_FILE
        
        ensure_output_dir()
        
        report = self.get_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Timing report saved to {output_path}")
        return output_path

# Global timing tracker instance
_tracker = TimingTracker()

def get_tracker() -> TimingTracker:
    """Get the global timing tracker instance."""
    return _tracker

def start_pipeline():
    """Start the pipeline timing."""
    _tracker.start_pipeline()

def end_pipeline():
    """End the pipeline timing."""
    _tracker.end_pipeline()

def start_stage(stage_name: str):
    """Start timing a specific stage."""
    _tracker.start_stage(stage_name)

def end_stage(stage_name: str):
    """End timing a specific stage."""
    _tracker.end_stage(stage_name)

@contextmanager
def timed_stage(stage_name: str):
    """Context manager for timing a stage."""
    _tracker.start_stage(stage_name)
    try:
        yield
    finally:
        _tracker.end_stage(stage_name)

def save_timing_report(output_path: Optional[str] = None) -> str:
    """Save the timing report to a JSON file."""
    return _tracker.save_report(output_path)

def main():
    """
    Main function to demonstrate timing instrumentation.
    
    This function simulates a pipeline execution with multiple stages
    and generates a timing report.
    """
    logger.info("Starting timing instrumentation demonstration")
    
    try:
        start_pipeline()
        
        # Simulate pipeline stages
        with timed_stage("data_download"):
            time.sleep(0.1)  # Simulate work
        
        with timed_stage("feature_extraction"):
            time.sleep(0.1)  # Simulate work
        
        with timed_stage("model_training"):
            time.sleep(0.1)  # Simulate work
        
        with timed_stage("evaluation"):
            time.sleep(0.1)  # Simulate work
        
        end_pipeline()
        
        # Save the report
        output_path = save_timing_report()
        logger.info(f"Timing report generated at: {output_path}")
        
        # Print summary
        report = _tracker.get_report()
        print(f"\nPipeline Execution Summary:")
        print(f"  Total Duration: {report['total_duration_seconds']:.3f} seconds")
        print(f"  Stages Executed: {report['metadata']['total_stages']}")
        if 'stage_summary' in report:
            print(f"  Average Stage Duration: {report['stage_summary']['avg_duration']:.3f} seconds")
        
    except Exception as e:
        logger.error(f"Error during timing instrumentation: {e}")
        raise

if __name__ == "__main__":
    main()