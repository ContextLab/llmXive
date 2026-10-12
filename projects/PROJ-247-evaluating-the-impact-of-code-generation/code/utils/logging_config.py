import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def setup_project_logging(name: str, log_file: str = "run.log"):
    """
    Configures logging for the project. 
    Logs are written to the directory specified by LOG_PATH in .env.
    """
    log_dir = os.getenv("LOG_PATH", "data/logs/")
    log_path = Path(log_dir) / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)
