import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def save_correlation_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save correlation results to JSON."""
    ensure_directories(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Correlation results saved to {output_path}")

def save_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save regression results to JSON."""
    ensure_directories(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Regression results saved to {output_path}")

def main() -> None:
    """Main entry point for saving results (if called as script)."""
    logger.warning("save_results.py is a utility module. Use model.py or report_generator.py to trigger saves.")

if __name__ == "__main__":
    main()
