"""
Pytest configuration and fixtures for integration tests.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure code directory is in path for imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set up environment variables if not present
if not os.getenv("COD_URL"):
    os.environ["COD_URL"] = "https://www.crystallography.net/cod/"

if not os.getenv("DATA_PATH"):
    # Default to a temp-like structure for tests if not set
    os.environ["DATA_PATH"] = str(root_dir / "data")
