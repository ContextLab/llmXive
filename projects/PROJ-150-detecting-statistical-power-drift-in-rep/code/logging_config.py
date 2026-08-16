import os
import logging
import sys
from pathlib import Path

def setup_logging():
    """Sets up basic logging configuration."""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stdout  # Log to stdout
    )

def get_module_logger(name):
    """Returns a logger for the given module."""
    return logging.getLogger(name)

def log_operation_start(op_name):
  """Logs the start of an operation."""
  logger = get_module_logger(__name__)
  logger.info(f"Starting operation: {op_name}")

def log_operation_complete(op_name):
  """Logs the completion of an operation."""
  logger = get_module_logger(__name__)
  logger.info(f"Completed operation: {op_name}")

def log_data_filter_step(rows_filtered, reason):
    """Logs data filtering steps."""
    logger = get_module_logger(__name__)
    logger.warning(f"Filtered {rows_filtered} rows due to {reason}")

def log_row_skip(index, reason):
  """Logs skipped row details."""
  logger = get_module_logger(__name__)
  logger.warning(f"Skipping row {index} due to: {reason}")