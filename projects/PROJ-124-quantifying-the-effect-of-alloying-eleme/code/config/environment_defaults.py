"""
Default environment configuration generator.

This module provides utilities to create default configuration files
when they don't exist, ensuring the pipeline can start with sensible defaults.
"""

from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "random_seed": 42,
    "datasets": {
        "gfa_recent": {
            "name": "Recent Experimental GFA Data",
            "url": "https://huggingface.co/datasets/GFA-D/pilot_flags/resolve/main/gfa_dataset.csv",
            "local_path": "data/raw/gfa_dataset.csv",
            "description": "Recent experimental glass-forming ability dataset with compositions and Rc values"
        },
        "known_alloys": {
            "name": "Known Alloys Database",
            "url": "https://raw.githubusercontent.com/llmXive/data/main/known_alloys.csv",
            "local_path": "data/known_alloys.csv",
            "description": "Database of known metallic glass compositions for novelty checking"
        }
    },
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "state": "state",
        "output": "output",
        "models": "code/models",
        "figures": "figures",
        "contracts": "contracts"
    },
    "experimental": {
        "use_weighted_models": True,
        "use_pca_doa_fallback": False,
        "enable_detailed_logging": True
    }
}

CONFIG_FILE_NAME = "environment.yaml"
CONFIG_DIR = Path("code/config")

def create_default_config(output_path: Path = None) -> Path:
    """
    Create a default environment configuration file.

    Args:
        output_path: Where to save the config file. If None, saves to code/config/environment.yaml

    Returns:
        Path to the created configuration file.
    """
    if output_path is None:
        output_path = CONFIG_DIR / CONFIG_FILE_NAME

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file already exists
    if output_path.exists():
        logger.warning(f"Configuration file already exists at {output_path}. Not overwriting.")
        return output_path

    # Write default configuration
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Created default configuration at {output_path}")
    return output_path

def main():
    """Main function to create default configuration."""
    logging.basicConfig(level=logging.INFO)
    config_path = create_default_config()
    print(f"Default configuration created at: {config_path}")

if __name__ == "__main__":
    main()