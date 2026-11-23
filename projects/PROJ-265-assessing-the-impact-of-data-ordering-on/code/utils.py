import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from config import get_project_root, get_results_dir

def setup_logging():
    """Configure logging for the project."""
    log_dir = os.path.join(get_project_root(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def calculate_checksum(data: str) -> str:
    """Calculate SHA256 checksum of a string."""
    return hashlib.sha256(data.encode()).hexdigest()

def verify_checksum(data: str, expected: str) -> bool:
    """Verify if the checksum of data matches the expected value."""
    return calculate_checksum(data) == expected

def log_simulation_result(result: Dict[str, Any]):
    """Log a single simulation result."""
    logger = logging.getLogger(__name__)
    logger.info(f"Result: phi={result.get('phi')}, n={result.get('n')}, "
                f"ordered_cov={result.get('ordered_coverage')}, "
                f"shuffled_cov={result.get('shuffled_coverage')}, "
                f"p_value={result.get('p_value')}")

def load_simulation_logs(filepath: str) -> list:
    """Load simulation logs from a JSON file."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)
