"""
Verification script for T008: Setup logging infrastructure.
Runs a dummy pipeline start/stop to ensure data/pipeline.log is created with entries.
"""
import sys
from pathlib import Path
from logging_config import setup_logging, log_pipeline_step, log_exclusion, get_logger

def main():
    """
    Executes a dummy pipeline sequence to verify logging infrastructure.
    """
    print("Starting T008 verification: Logging Infrastructure Setup")
    
    # Initialize the logger (this creates the file handler and directory if needed)
    logger = setup_logging()
    
    # Log a pipeline start
    log_pipeline_step("PIPELINE_START", "Verification run for T008")
    
    # Simulate a step
    log_pipeline_step("DATA_LOADING", "Loading stimuli and ratings")
    
    # Simulate an exclusion event (straight-lining)
    log_exclusion("STRAIGHT_LINING", participant_id="P-VERIFICATION-001")
    
    # Simulate another step
    log_pipeline_step("ANALYSIS_COMPLETE", "Dummy analysis finished")
    
    # Log pipeline stop
    log_pipeline_step("PIPELINE_STOP", "Verification run completed")
    
    # Verify the file exists
    from config import get_processed_data_dir
    log_file_path = get_processed_data_dir().parent / "pipeline.log"
    
    if not log_file_path.exists():
        print(f"ERROR: Log file {log_file_path} was not created.")
        sys.exit(1)
    
    # Verify it has content
    content = log_file_path.read_text()
    if not content.strip():
        print(f"ERROR: Log file {log_file_path} is empty.")
        sys.exit(1)
    
    # Verify specific entries are present
    required_entries = [
        "PIPELINE_START",
        "STRAIGHT_LINING",
        "PIPELINE_STOP"
    ]
    
    missing = []
    for entry in required_entries:
        if entry not in content:
            missing.append(entry)
    
    if missing:
        print(f"ERROR: Log file missing required entries: {missing}")
        sys.exit(1)
    
    print(f"SUCCESS: Log file created at {log_file_path}")
    print("Content preview:")
    print("-" * 40)
    print(content)
    print("-" * 40)
    print("T008 Verification Passed.")

if __name__ == "__main__":
    main()