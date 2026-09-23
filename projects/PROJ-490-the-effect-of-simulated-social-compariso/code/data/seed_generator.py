import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config

logger = get_logger(__name__)

# Ground Truth Parameters (FR-011)
SYNTHETIC_PARAMS = {
    "intercept": 0.0,
    "main_effect_avatar": 0.1,
    "main_effect_comparison": 0.1,
    "interaction_beta": 0.2,
    "noise_sigma": 1.0,
    "n_samples": 150
}

def generate_seed_file(seed: int, output_path: Optional[Path] = None):
    """
    Generate the synthetic seed JSON file.
    
    Args:
        seed: Random seed value
        output_path: Optional path to save the file. Defaults to data/raw/synthetic_seed.json
    """
    log_execution_start(logger, "generate_seed_file")
    
    config = get_config()
    if output_path is None:
        raw_path = config.get("paths", {}).get("raw_data", config.project_root / "data" / "raw")
        raw_path.mkdir(parents=True, exist_ok=True)
        output_path = raw_path / "synthetic_seed.json"
    
    seed_data = {
        "seed": seed,
        "parameters": SYNTHETIC_PARAMS,
        "generated_at": datetime.utcnow().isoformat(),
        "label": "Pipeline Validation Only"
    }
    
    with open(output_path, 'w') as f:
        json.dump(seed_data, f, indent=2)
    
    logger.info(f"Seed file generated: {output_path}")
    log_execution_end(logger, "generate_seed_file", success=True)

def main():
    """Entry point."""
    try:
        config = get_config()
        generate_seed_file(config.seed)
    except Exception as e:
        logger.error(f"Seed generation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
