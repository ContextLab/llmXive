"""
Install project dependencies from requirements.txt and initialize reproducibility seeds.

This script is intended to be run as part of the project quick-start. It installs the
packages listed in ``requirements.txt`` using the current Python interpreter and then
calls :func:`utils.seed.set_seeds` to fix all relevant random seeds.

The script exits with a non-zero status if the installation fails or if the seed
initialisation raises an exception.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

# Make the repository's ``code/`` directory importable so that
# ``utils.seed`` resolves regardless of the working directory.
_CODE_DIR = Path(__file__).resolve().parents[1]
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

# Import the seed helper (the module is part of the repository).
try:
    from utils.seed import set_seeds
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "Failed to import utils.seed. Ensure the repository's code/ "
        "directory is on PYTHONPATH."
    ) from exc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def _install_requirements(requirements_path: Path) -> None:
    """Install the packages listed in ``requirements.txt`` using pip."""
    if not requirements_path.is_file():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")

    logger.info("Installing dependencies from %s", requirements_path)
    # Use the same interpreter that runs this script.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])

def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Install project dependencies and initialise reproducibility seeds."
    )
    parser.add_argument(
        "--requirements",
        type=str,
        default=str(_CODE_DIR.parent / "requirements.txt"),
        help="Path to the requirements file (default: requirements.txt at the project root).",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip pip installation (useful when dependencies are preinstalled).",
    )
    args = parser.parse_args()

    req_path = Path(args.requirements)
    if not args.skip_install:
        _install_requirements(req_path)
    else:
        logger.info("Skipping pip installation (--skip-install).")

    # Initialise deterministic seeds after the environment is ready.
    logger.info("Setting reproducibility seeds.")
    summary = set_seeds()  # uses the default seed (42)
    logger.info("Seed summary: %s", summary)
    logger.info("Setup completed successfully.")

if __name__ == "__main__":
    main()
