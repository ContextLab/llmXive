"""
llmXive research pipeline for predicting the influence of alloying on the glass transition temperature of metallic glasses.
"""

__version__ = "0.1.0"

import logging
import os
from pathlib import Path

# Ensure logs directory exists
logs_dir = Path("logs")
logs_dir.mkdir(parents=True, exist_ok=True)

# Configure default logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "ingest.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
