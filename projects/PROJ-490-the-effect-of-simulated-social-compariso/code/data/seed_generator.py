"""
Seed File Generation Module (T011c)

Implements the generation of the synthetic seed file (data/raw/synthetic_seed.json)
containing the ground truth parameters used to generate synthetic data.
This ensures reproducibility and transparency as per FR-009.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from data.config import get_config
from utils.logger import get_logger

# Configure logger for this module
logger = get_logger(__name__)


def generate_seed_file(
    output_path: Optional[Path] = None,
    ground_truth_params: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Generate the synthetic seed file containing ground truth parameters.

    This function creates `data/raw/synthetic_seed.json` with the parameters
    used to generate the synthetic dataset. If no parameters are provided,
    it uses the hardcoded ground truth values defined in the task specification.

    Args:
        output_path: Optional custom output path. Defaults to `data/raw/synthetic_seed.json`.
        ground_truth_params: Optional dictionary of ground truth parameters.
                             If None, uses the standard task parameters.

    Returns:
        Path to the generated seed file.

    Raises:
        FileNotFoundError: If the output directory does not exist.
        IOError: If the file cannot be written.
    """
    config = get_config()
    project_root = config.project_root
    raw_data_dir = project_root / "data" / "raw"

    # Ensure directory exists
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = raw_data_dir / "synthetic_seed.json"

    # Default Ground Truth Parameters (from T010 specification)
    # intercept=0, main_effect_avatar=0.1, main_effect_comparison=0.1,
    # interaction_beta=0.2, noise_sigma=1.0
    if ground_truth_params is None:
        ground_truth_params = {
            "intercept": 0.0,
            "main_effect_avatar": 0.1,
            "main_effect_comparison": 0.1,
            "interaction_beta": 0.2,
            "noise_sigma": 1.0,
            "sample_size": 100,  # Minimum N >= 100 as per FR-001
            "random_seed": config.seed,
            "label": "Pipeline Validation Only"
        }

    seed_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "task_id": "T011c",
            "description": "Ground truth parameters for synthetic data generation",
            "data_source_type": "synthetic"
        },
        "ground_truth_parameters": ground_truth_params
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(seed_data, f, indent=2)
        
        logger.info(f"Successfully generated synthetic seed file: {output_path}")
        logger.debug(f"Seed content: {json.dumps(seed_data, indent=2)}")
    except IOError as e:
        logger.error(f"Failed to write seed file to {output_path}: {e}")
        raise IOError(f"Failed to write seed file: {e}") from e

    return output_path


def main():
    """
    Main entry point for the seed generation script.
    """
    logger.info("Starting seed file generation (T011c)...")
    try:
        output_path = generate_seed_file()
        logger.info(f"Seed file generation complete. Output: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Seed file generation failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
