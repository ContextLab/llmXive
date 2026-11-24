import seed
import subprocess
import sys
import logging
from pathlib import Path

def main():
    """Install dependencies from requirements.txt."""
    req_path = Path("requirements.txt")
    if not req_path.is_file():
        logging.error("requirements.txt not found.")
        sys.exit(1)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])
