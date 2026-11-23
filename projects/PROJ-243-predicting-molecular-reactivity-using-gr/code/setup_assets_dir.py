import os
import sys
import logging
from typing import Optional

from config import get_config, ensure_directories


def setup_script_logging() -> logging.Logger:
    """Initialize logging for the setup_assets_dir script."""
    logger = logging.getLogger("setup_assets_dir")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger


def create_assets_directory(logger: Optional[logging.Logger] = None) -> None:
    """
    Create the `data/assets` directory if it does not exist.

    This task fulfills T001c: Create data directory: `data/assets`.
    """
    if logger is None:
        logger = setup_script_logging()

    config = get_config()
    # ensure_directories is called to create the base structure defined in config.
    # However, to explicitly satisfy T001c, we ensure the specific path exists.
    assets_path = os.path.join(config.get("data_dir", "data"), "assets")

    logger.info(f"Ensuring assets directory exists: {assets_path}")

    if not os.path.exists(assets_path):
        os.makedirs(assets_path, exist_ok=True)
        logger.info(f"Created directory: {assets_path}")
    else:
        logger.info(f"Directory already exists: {assets_path}")

    # Verify it is a directory
    if not os.path.isdir(assets_path):
        raise RuntimeError(f"Path exists but is not a directory: {assets_path}")

    logger.info("Assets directory setup complete.")


def main() -> None:
    """Entry point for the script."""
    logger = setup_script_logging()
    try:
        create_assets_directory(logger)
    except Exception as e:
        logger.error(f"Failed to create assets directory: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()