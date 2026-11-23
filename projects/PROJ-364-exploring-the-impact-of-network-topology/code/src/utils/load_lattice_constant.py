"""
Utility to load and inject the lattice resistance constant into the runtime configuration.

This script reads the version-controlled `src/constants/lattice_resistance.yaml`
and updates the global Config object with the `R_lattice` value.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_config, ConfigError
from src.utils.checksum import calculate_sha256

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONSTANTS_FILE_PATH = "src/constants/lattice_resistance.yaml"


def load_lattice_constant() -> float:
    """
    Loads the R_lattice value from the constants YAML file.

    Returns:
        float: The lattice resistance value.

    Raises:
        FileNotFoundError: If the constants file does not exist.
        ConfigError: If the file is malformed or R_lattice is missing.
    """
    config_path = PROJECT_ROOT / CONSTANTS_FILE_PATH

    if not config_path.exists():
        raise FileNotFoundError(
            f"Lattice resistance constant file not found at {config_path}. "
            "Ensure T005b has been completed."
        )

    try:
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ConfigError(f"YAML file {config_path} is empty or invalid.")

        if 'R_lattice' not in data:
            raise ConfigError(
                f"Key 'R_lattice' not found in {config_path}. "
                "Expected format: R_lattice: <float>"
            )

        value = data['R_lattice']
        if not isinstance(value, (int, float)):
            raise ConfigError(f"R_lattice must be a number, got {type(value)}")

        # Verify checksum for reproducibility tracking (optional but good practice)
        checksum = calculate_sha256(str(config_path))
        logger.info(f"Loaded R_lattice={value} from {config_path} (SHA256: {checksum[:8]}...)")

        return float(value)

    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML in {config_path}: {e}") from e
    except Exception as e:
        raise ConfigError(f"Unexpected error loading lattice constant: {e}") from e


def inject_into_config() -> None:
    """
    Loads the constant and injects it into the global configuration singleton.
    This ensures downstream modules (e.g., src/data/materials.py) see the value.
    """
    try:
        r_lattice = load_lattice_constant()
        config = get_config()
        
        # Inject into the config dict if not already present or to ensure override
        if 'R_lattice' not in config:
            config['R_lattice'] = r_lattice
            logger.info(f"Injected R_lattice={r_lattice} into runtime config.")
        else:
            logger.info(f"R_lattice already present in config: {config['R_lattice']}")
            
    except (FileNotFoundError, ConfigError) as e:
        logger.error(f"Failed to inject lattice constant: {e}")
        raise


def main():
    """
    Entry point for running this script as a module or CLI.
    """
    logger.info("Starting lattice constant injection...")
    inject_into_config()
    logger.info("Lattice constant injection complete.")


if __name__ == "__main__":
    main()
