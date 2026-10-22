"""
Install project dependencies from requirements.txt and initialize reproducibility seeds.

This script is intended to be run as part of the project quick‑start. It installs the
packages listed in ``requirements.txt`` using the current Python interpreter and then
calls :func:`utils.seed.set_seeds` to fix all relevant random seeds.

The script exits with a non‑zero status if the installation fails or if the seed
initialisation raises an exception.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

# Import the seed helper after it has been installed (the module is part of the
# repository, not an external dependency).
try:
    from utils.seed import set_seeds
except Exception as exc:  # pragma: no cover
    # The import will work once the repository is on the Python path; if it fails
    # we still want a clear error message.
    raise ImportError("Failed to import utils.seed. Ensure the repository root is on PYTHONPATH.") from exc

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
        default="requirements.txt",
        help="Path to the requirements file (default: requirements.txt).",
    )
    args = parser.parse_args()

    req_path = Path(args.requirements)
    _install_requirements(req_path)

    # Initialise deterministic seeds after the environment is ready.
    logger.info("Setting reproducibility seeds.")
    set_seeds()  # uses the default seed (42)
    logger.info("Setup completed successfully.")

if __name__ == "__main__":
    main()
