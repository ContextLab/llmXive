import logging
import sys
import os
from pathlib import Path

# Ensure logs directory exists before configuring handlers
project_root = Path(__file__).parent.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

log_file_path = logs_dir / "pipeline.log"

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    ]
)

# Create module-level logger
logger = logging.getLogger(__name__)
logger.info("Logging infrastructure initialized.")

# Error handling helper
class PipelineError(Exception):
    """Custom exception for pipeline-specific errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        logger.error(f"PipelineError: {message}", extra={"details": self.details})

def handle_error(e: Exception, context: str = "Unknown context") -> None:
    """Centralized error handling to log exceptions with context."""
    logger.error(f"Error in {context}: {type(e).__name__}: {e}", exc_info=True)
    if isinstance(e, PipelineError):
        raise e
    raise PipelineError(f"Unexpected error in {context}", {"original_error": str(e), "type": type(e).__name__}) from e

logger.info("Error handling infrastructure ready.")