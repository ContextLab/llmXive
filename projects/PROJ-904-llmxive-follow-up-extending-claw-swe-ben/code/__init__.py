"""
llmXive Automated Science Pipeline - Code Package.

This package contains the core implementation for the Context Fidelity vs. Model Scaling Trade-offs research.
"""
import logging
import sys
from pathlib import Path

# Ensure the code directory is in the path for relative imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

# Configure root logger for the package
def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger for the package."""
    logger = logging.getLogger()
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

# Initialize logging immediately
setup_logging()
