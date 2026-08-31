"""
Configuration Generator for Molecular Permeability Project.

This script programmatically generates `config.yaml` with parameters
explicitly linked to Functional Requirements defined in the project spec.

Parameters:
1. validation.require_experimental_target: Allows Proxy Mode (FR-000/Plan Phase 0).
2. validation.bias_threshold: Controls FR-013 bias check.
3. validation.retention_threshold: Controls FR-011 retention check.
4. validation.stratification_difference_threshold: Controls FR-003 stratification check.
"""

import yaml
import logging
import os
from pathlib import Path
from datetime import datetime

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_config(output_path: Path) -> dict:
    """
    Generate the configuration dictionary based on Functional Requirements.

    Args:
        output_path: Path where the config.yaml file will be written.

    Returns:
        The generated configuration dictionary.
    """
    config = {
        "project": {
            "id": "PROJ-422-predicting-molecular-permeability-coeffi",
            "name": "Predicting Molecular Permeability Coefficients Using GNNs",
            "generated_at": datetime.now().isoformat()
        },
        "validation": {
            # FR-000 / Plan Phase 0: Allows Proxy Mode for feasibility study
            # If true, pipeline requires experimental target; if false, allows calculated logP.
            "require_experimental_target": False,
            
            # FR-013: Bias Check Threshold
            # Controls the maximum allowed correlation between input descriptors 
            # and target before flagging a potential confound.
            "bias_threshold": 0.85,
            
            # FR-011: Retention Threshold
            # Minimum percentage of valid molecules required to proceed.
            # Enforced strictly; pipeline halts if valid retention < this value.
            "retention_threshold": 0.95,
            
            # FR-003: Stratification Difference Threshold
            # Maximum allowed difference in class distribution between train/test splits.
            # Default 0.05 (5%) aligns with standard statistical significance criteria.
            "stratification_difference_threshold": 0.05
        },
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "interim_dir": "data/interim"
        },
        "models": {
            "gnn": {
                "hidden_dim": 128,
                "num_layers": 3,
                "dropout": 0.1
            },
            "rf": {
                "n_estimators": 100,
                "max_depth": None
            }
        },
        "training": {
            "batch_size": 32,
            "epochs": 50,
            "early_stopping_patience": 10,
            "cpu_only": True
        }
    }

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Configuration generated successfully at: {output_path}")
    return config

def main():
    """Entry point for the configuration generation script."""
    # Determine output path relative to project root
    # Assuming script is run from project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config.yaml"
    
    logger.info(f"Generating config at: {config_path}")
    config = generate_config(config_path)
    
    # Verify content by printing keys
    logger.info("Config keys generated:")
    for key in config:
        logger.info(f"  - {key}")

if __name__ == "__main__":
    main()