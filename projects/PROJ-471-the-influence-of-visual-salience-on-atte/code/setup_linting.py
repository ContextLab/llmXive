"""
Setup script to initialize linting and formatting configurations.
This script ensures that ruff and black configurations exist and are valid.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger

logger = get_logger("setup_linting")

def main():
    """
    Main entry point for setting up linting configurations.
    Verifies that configuration files exist and are syntactically valid.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    logger.info("Starting linting setup...")

    # Verify ruff configuration
    ruff_config = code_dir / ".ruff.toml"
    if ruff_config.exists():
        logger.info(f"Ruff configuration found at {ruff_config}")
        # Validate syntax by attempting to parse as TOML
        try:
            import tomllib
            with open(ruff_config, "rb") as f:
                tomllib.load(f)
            logger.info("Ruff configuration is valid TOML.")
        except ImportError:
            # Python < 3.11 fallback
            try:
                import toml
                with open(ruff_config, "r") as f:
                    toml.load(f)
                logger.info("Ruff configuration is valid TOML (using toml lib).")
            except Exception as e:
                logger.error(f"Ruff configuration parsing failed: {e}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Ruff configuration parsing failed: {e}")
            sys.exit(1)
    else:
        logger.error(f"Ruff configuration missing at {ruff_config}")
        sys.exit(1)

    # Verify black configuration
    black_config = code_dir / ".black.toml"
    if black_config.exists():
        logger.info(f"Black configuration found at {black_config}")
        try:
            import tomllib
            with open(black_config, "rb") as f:
                tomllib.load(f)
            logger.info("Black configuration is valid TOML.")
        except ImportError:
            try:
                import toml
                with open(black_config, "r") as f:
                    toml.load(f)
                logger.info("Black configuration is valid TOML (using toml lib).")
            except Exception as e:
                logger.error(f"Black configuration parsing failed: {e}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Black configuration parsing failed: {e}")
            sys.exit(1)
    else:
        logger.error(f"Black configuration missing at {black_config}")
        sys.exit(1)

    logger.info("Linting setup completed successfully.")

if __name__ == "__main__":
    main()
