"""
llmXive research pipeline for predicting the influence of alloying on the glass transition temperature of metallic glasses.
"""

__version__ = "0.1.0"

import logging
import os
from pathlib import Path

# ----------------------------------------------------------------------
# Project directory setup (required by T001 verification)
# ----------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent

# Directories that must exist for the pipeline
required_dirs = [
    project_root / "data" / "raw",
    project_root / "data" / "processed",
    project_root / "artifacts" / "models",
    project_root / "artifacts" / "metrics",
    project_root / "artifacts" / "reports",
    project_root / "tests",
    project_root / "specs" / "001-predicting-the-influence-of-alloying-on" / "contracts",
    project_root / "logs",
]

for d in required_dirs:
    d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Configure default logging (writes to logs/ingest.log by default)
# ----------------------------------------------------------------------
logs_dir = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "ingest.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
