"""
Generate configuration file for the molecular permeability prediction pipeline.

This script programmatically generates a `config.yaml` file with configurable
parameters required for the pipeline execution, including thresholds for bias,
retention, stratification, and proxy target columns.
"""
import yaml
import logging
import os
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_config(output_path: Path) -> None:
    """
    Generate the config.yaml file with default and configurable parameters.
    
    Args:
        output_path: Path where the config.yaml file will be written.
    """
    config = {
        "pipeline": {
            "name": "Molecular Permeability Prediction",
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat()
        },
        "data": {
            "source": "huggingface/datasets/chembl_v30",
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "interim_dir": "data/interim"
        },
        "thresholds": {
            "bias_threshold": 0.85,
            "retention_threshold": 0.95,
            "stratification_diff_threshold": 0.05
        },
        "modeling": {
            "proxy_target_columns": ["logP", "calculated_logP"],
            "staged_mode": False,
            "early_stopping_patience": 5,
            "cpu_only": True
        },
        "evaluation": {
            "metrics": ["rmse", "mae", "r2"],
            "significance_level": 0.05
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        }
    }

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the configuration to YAML
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Configuration file generated successfully at: {output_path}")

def main():
    """Main entry point for the script."""
    # Determine the project root relative to this script
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent  # projects/PROJ-422-...
    config_path = project_root / "config.yaml"

    logger.info(f"Generating configuration at: {config_path}")
    generate_config(config_path)

    # Verify the file was created
    if config_path.exists():
        logger.info("Verification: config.yaml exists.")
        # Optionally print a summary
        with open(config_path, 'r') as f:
            logger.info(f"Content preview:\n{f.read()}")
    else:
        logger.error("Verification failed: config.yaml was not created.")
        raise FileNotFoundError(f"Failed to create {config_path}")

if __name__ == "__main__":
    main()
