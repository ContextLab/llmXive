import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config, ensure_directories
from robustness import run_robustness_check

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"SAVE_ROB: {message}")

def save_robustness_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save robustness results to JSON file."""
    _log_step(f"Saving robustness results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def main() -> None:
    """Main entry point for saving robustness results script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    input_path = Path("data/processed/analysis_data.csv")
    output_path = Path("outputs/robustness_results.json")
    
    try:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        import pandas as pd
        df = pd.read_csv(input_path)
        results = run_robustness_check(df)
        
        save_robustness_results(results, output_path)
        logger.info(f"Robustness results saved to {output_path}")
    except Exception as e:
        logger.error(f"Save robustness results failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
