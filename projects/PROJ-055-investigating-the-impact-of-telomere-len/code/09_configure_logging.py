"""
Script to configure and demonstrate logging infrastructure.

This script initializes the logging system, writes test logs to the logs/ directory,
and demonstrates memory pressure detection capabilities.
"""
import sys
import time
from pathlib import Path
from logging_config import init_project_logging, handle_memory_pressure, log_memory_status

def main():
    """Main entry point for logging configuration demonstration."""
    # Initialize project logging
    logger = init_project_logging(log_file="test_config.log", log_level="DEBUG")
    
    logger.info("Starting logging configuration demonstration")
    
    # Log memory status
    log_memory_status(logger)
    
    # Simulate some operations
    logger.info("Simulating data processing operations...")
    time.sleep(0.1)
    
    # Check memory pressure
    pressure_detected = handle_memory_pressure(logger)
    
    if pressure_detected:
        logger.warning("Memory pressure detected - recommendations: enable chunked processing")
    else:
        logger.info("Memory usage within acceptable limits")
    
    # Log final status
    logger.info("Logging configuration demonstration completed")
    logger.info(f"Log file written to: {Path('logs') / 'test_config.log'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
