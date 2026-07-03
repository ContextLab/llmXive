"""
Main entry point for the Mitochondrial Aging Correlation analysis pipeline.

Implements runtime timing and structured logging infrastructure as per T005.
This script orchestrates the execution of the analysis pipeline, measuring
execution time for each phase and logging events to both console and file.
"""
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
def setup_logging(log_file: str = "analysis.log") -> logging.Logger:
    """
    Configure logging to output to both console and file.
    
    Args:
        log_file: Name of the log file within the logs directory.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("mito_aging_pipeline")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # File handler
    log_path = LOGS_DIR / log_file
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    return logger

class AnalysisTimer:
    """
    Context manager and utility class for timing pipeline phases.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
        self.total_start_time = None
        self.phase_durations = {}

    def start_total(self):
        """Start the overall pipeline timer."""
        self.total_start_time = time.time()
        self.logger.info("Pipeline execution started.")

    def start_phase(self, phase_name: str):
        """Start timing a specific phase."""
        self.start_times[phase_name] = time.time()
        self.logger.info(f"--- Starting Phase: {phase_name} ---")

    def end_phase(self, phase_name: str):
        """End timing a specific phase and log duration."""
        if phase_name not in self.start_times:
            self.logger.warning(f"Phase '{phase_name}' was not started.")
            return
        
        end_time = time.time()
        duration = end_time - self.start_times[phase_name]
        self.phase_durations[phase_name] = duration
        self.logger.info(f"--- Completed Phase: {phase_name} (Duration: {duration:.2f}s) ---")

    def end_total(self):
        """End the overall pipeline timer and log summary."""
        if not self.total_start_time:
            self.logger.warning("Total timer was not started.")
            return
        
        end_time = time.time()
        total_duration = end_time - self.total_start_time
        
        self.logger.info("=" * 50)
        self.logger.info("PIPELINE EXECUTION SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total Runtime: {total_duration:.2f} seconds")
        self.logger.info("Phase Breakdown:")
        for phase, duration in self.phase_durations.items():
            self.logger.info(f"  - {phase}: {duration:.2f}s")
        self.logger.info("=" * 50)
        self.logger.info("Pipeline execution finished.")

def run_pipeline():
    """
    Main execution function for the analysis pipeline.
    
    This function demonstrates the logging and timing infrastructure
    by running a sequence of mock phases. In a full implementation,
    this would call the actual analysis modules (load_data, preprocess, model).
    """
    logger = setup_logging()
    timer = AnalysisTimer(logger)
    
    timer.start_total()
    
    try:
        # Phase 1: Data Availability Gate
        timer.start_phase("Data_Availability_Gate")
        # Placeholder for T007A/T007B logic
        time.sleep(0.1) # Simulate check
        timer.end_phase("Data_Availability_Gate")

        # Phase 2: Data Loading & Preprocessing
        timer.start_phase("Data_Loading_Preprocessing")
        # Placeholder for T012-T020 logic
        time.sleep(0.1) # Simulate processing
        timer.end_phase("Data_Loading_Preprocessing")

        # Phase 3: Statistical Modeling
        timer.start_phase("Statistical_Modeling")
        # Placeholder for T023-T028 logic
        time.sleep(0.1) # Simulate modeling
        timer.end_phase("Statistical_Modeling")

        # Phase 4: Sensitivity Analysis
        timer.start_phase("Sensitivity_Analysis")
        # Placeholder for T032-T038 logic
        time.sleep(0.1) # Simulate sensitivity check
        timer.end_phase("Sensitivity_Analysis")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise
    finally:
        timer.end_total()

if __name__ == "__main__":
    run_pipeline()