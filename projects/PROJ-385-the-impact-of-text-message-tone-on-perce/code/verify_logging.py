import sys
from pathlib import Path
from config import get_project_root
from logging_config import setup_logging, log_pipeline_step, log_exclusion, get_logger

def main():
    """
    Verification script for T008: Setup logging infrastructure.
    Runs a dummy pipeline start/stop to ensure data/pipeline.log is created with entries.
    """
    # Initialize the logger (this creates the file handler)
    logger = setup_logging()
    
    # Simulate pipeline steps
    log_pipeline_step("Pipeline Start: Dummy Run")
    log_pipeline_step("Data Loading Simulation")
    
    # Simulate an exclusion event (e.g., straight-lining or missing data)
    log_exclusion("Straight-lining detected (zero variance)", "P-12345")
    log_exclusion("Missing data (incomplete stimulus set)", "P-67890")
    
    log_pipeline_step("Pipeline End: Dummy Run")
    
    print("Logging verification complete. Check data/pipeline.log for entries.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
