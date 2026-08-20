import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def save_robustness_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save robustness results to JSON."""
    ensure_directories(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Robustness results saved to {output_path}")

def main() -> None:
    """Main entry point."""
    logger.warning("save_robustness_results.py is a utility module. Use robustness.py to trigger saves.")

if __name__ == "__main__":
    main()
