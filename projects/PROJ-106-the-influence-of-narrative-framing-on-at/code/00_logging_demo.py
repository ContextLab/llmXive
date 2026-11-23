"""
Demonstration script for the logging infrastructure.
This script shows how to use the logging utilities for audit trails.
"""
import sys
import json
from pathlib import Path

# Add code directory to path
sys.path.insert(0, 'code')

from utils.logger import (
    setup_logger, 
    log_script_start, 
    log_script_end, 
    log_data_operation, 
    log_analysis_step,
    log_audit_event,
    log_exception
)

def main():
    """Run a demonstration of the logging infrastructure."""
    # Setup logger
    logger = setup_logger("demo_logging")
    
    # Log script start
    log_script_start(logger, "00_logging_demo.py")
    
    try:
        # Simulate data operations
        log_data_operation(logger, "initialize_environment", None)
        log_data_operation(logger, "load_configuration", 1)
        
        # Simulate data processing
        log_data_operation(logger, "process_records", 100)
        log_data_operation(logger, "validate_data", 100)
        
        # Simulate analysis steps
        analysis_result = {"mean": 42.5, "std": 10.2, "n": 100}
        log_analysis_step(logger, "calculate_descriptive_stats", analysis_result)
        
        # Simulate audit events
        log_audit_event(logger, "DATA_ACCESS", {"user": "system", "action": "read"})
        log_audit_event(logger, "DATA_MODIFICATION", {"user": "system", "action": "write", "records": 50})
        
        # Simulate successful completion
        log_script_end(logger, "00_logging_demo.py", True)
        
        print("Logging demo completed successfully. Check data/logs/ for log files.")
        
    except Exception as e:
        log_exception(logger, e)
        log_script_end(logger, "00_logging_demo.py", False)
        print(f"Logging demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()