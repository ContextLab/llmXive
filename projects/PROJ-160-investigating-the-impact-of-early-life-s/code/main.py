"""
Main entry point for the Early Life Stress Impact Analysis Pipeline.

This module orchestrates the entire pipeline: data acquisition, preprocessing,
statistical modeling, and robustness validation. It includes comprehensive
error handling and JSON-formatted logging to logs/pipeline.log.
"""
import json
import logging
import logging.handlers
import os
import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# Import project configuration
from code.config import (
    get_project_root,
    get_logs_dir,
    ensure_directories,
    get_data_dir,
    get_processed_dir
)
from code.data.acquisition import main as acquire_data_main
from code.data.preprocessing import main as preprocessing_main
from code.analysis.modeling import main as modeling_main
from code.analysis.robustness import main as robustness_main
from code.analysis.save_results import main as save_results_main
from code.analysis.aggregate_robustness import main as aggregate_robustness_main

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, stage: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.details = details or {}

class DataLoadError(PipelineError):
    """Exception raised when data loading fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, stage="DataLoading", details=details)

class ValidationError(PipelineError):
    """Exception raised when data validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, stage="Validation", details=details)

class AnalysisError(PipelineError):
    """Exception raised when statistical analysis fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, stage="Analysis", details=details)

class IOWriteError(PipelineError):
    """Exception raised when writing output files fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, stage="IOWrite", details=details)

# Logger setup
_logger: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure JSON logging to logs/pipeline.log and console output.
    
    Args:
        log_level: Minimum logging level (e.g., logging.INFO, logging.DEBUG)
        
    Returns:
        Configured logger instance
    """
    global _logger
    if _logger is not None:
        return _logger

    project_root = get_project_root()
    logs_dir = get_logs_dir()
    
    # Ensure logs directory exists
    try:
        ensure_directories()
    except Exception as e:
        print(f"CRITICAL: Failed to create logs directory: {e}", file=sys.stderr)
        raise

    # Create logger
    _logger = logging.getLogger("pipeline")
    _logger.setLevel(log_level)
    _logger.propagate = False

    # Clear existing handlers to avoid duplicates in repeated runs
    _logger.handlers.clear()

    # JSON File Handler
    log_file_path = logs_dir / "pipeline.log"
    try:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(log_level)
        
        # Custom JSON Formatter
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_record = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                if record.exc_info:
                    log_record["exception"] = {
                        "type": record.exc_info[0].__name__,
                        "message": str(record.exc_info[1]),
                        "traceback": traceback.format_exception(*record.exc_info)
                    }
                
                if hasattr(record, 'details'):
                    log_record["details"] = record.details
                
                return json.dumps(log_record)

        file_handler.setFormatter(JSONFormatter())
        _logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to standard formatting if JSON fails
        fallback_handler = logging.FileHandler(log_file_path)
        fallback_handler.setLevel(log_level)
        fallback_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        _logger.addHandler(fallback_handler)
        _logger.error(f"Failed to setup JSON logging, using fallback: {e}")

    # Console Handler (Standard formatting for readability)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    return _logger

def run_stage(stage_name: str, func, *args, **kwargs) -> Any:
    """
    Execute a pipeline stage with comprehensive error handling and logging.
    
    Args:
        stage_name: Name of the stage for logging
        func: Function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function execution
        
    Raises:
        PipelineError: If the stage fails
    """
    logger = logging.getLogger("pipeline")
    logger.info(f"Starting stage: {stage_name}", extra={"details": {"stage": stage_name}})
    
    try:
        result = func(*args, **kwargs)
        logger.info(f"Completed stage: {stage_name}", extra={"details": {"stage": stage_name, "status": "success"}})
        return result
    except DataLoadError as e:
        logger.error(f"Data loading failed in {stage_name}: {e.message}", extra={"details": e.details})
        raise
    except ValidationError as e:
        logger.error(f"Validation failed in {stage_name}: {e.message}", extra={"details": e.details})
        raise
    except AnalysisError as e:
        logger.error(f"Analysis failed in {stage_name}: {e.message}", extra={"details": e.details})
        raise
    except IOWriteError as e:
        logger.error(f"IO write failed in {stage_name}: {e.message}", extra={"details": e.details})
        raise
    except Exception as e:
        error_msg = f"Unexpected error in {stage_name}: {str(e)}"
        logger.exception(error_msg)
        raise PipelineError(error_msg, stage=stage_name, details={"exception": str(e)}) from e

def run_pipeline() -> bool:
    """
    Execute the full analysis pipeline.
    
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    logger = setup_logging()
    logger.info("Pipeline initialization started")
    
    try:
        # 1. Data Acquisition
        run_stage("Data Acquisition", acquire_data_main)
        
        # 2. Preprocessing
        run_stage("Preprocessing", preprocessing_main)
        
        # 3. Statistical Modeling
        run_stage("Statistical Modeling", modeling_main)
        
        # 4. Robustness Validation
        run_stage("Robustness Validation", robustness_main)
        
        # 5. Save Results
        run_stage("Save Results", save_results_main)
        
        # 6. Aggregate Robustness Metrics
        run_stage("Aggregate Robustness", aggregate_robustness_main)
        
        logger.info("Pipeline completed successfully")
        return True
        
    except PipelineError as e:
        logger.error(f"Pipeline failed at stage '{e.stage}': {e.message}")
        return False
    except Exception as e:
        logger.exception(f"Pipeline failed with unexpected error: {str(e)}")
        return False
    finally:
        logger.info("Pipeline execution finished")

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    success = run_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())