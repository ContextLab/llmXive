import sys
from pathlib import Path
from config import get_project_root
from logging_config import setup_logging, log_pipeline_step, log_exclusion, get_logger

def main():
    """
    Executes a dummy pipeline run to verify logging infrastructure.
    Creates data/pipeline.log with start/stop entries and exclusion examples.
    """
    # Ensure the log file path exists by running the setup
    logger = setup_logging()
    
    # Log the start of the dummy pipeline
    log_pipeline_step("Pipeline Start - Verification Run")
    
    # Simulate a processing step
    log_pipeline_step("Loading Stimuli")
    log_pipeline_step("Simulating Ratings")
    
    # Simulate exclusion events (as per task requirements)
    log_exclusion("straight-lining", "P-001")
    log_exclusion("missing_data", "P-042")
    
    # Log the end of the dummy pipeline
    log_pipeline_step("Pipeline End - Verification Run")
    
    print("Logging verification complete. Check data/pipeline.log for entries.")

if __name__ == "__main__":
    main()
