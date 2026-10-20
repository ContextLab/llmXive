import subprocess
import sys
import logging
from pathlib import Path

def main():
    # Configure simple console logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    # Locate the project's root requirements.txt
    req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    if not req_path.is_file():
        logger.error(f"requirements.txt not found at {req_path}")
        sys.exit(1)

    logger.info(f"Installing dependencies from {req_path}")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])
        logger.info("All dependencies installed successfully.")
    except subprocess.CalledProcessError as exc:
        logger.error(f"Dependency installation failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)

if __name__ == "__main__":
    main()