"""
Configuration loader for the project.
Defines API endpoints and global constants.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Constants
YEAR_RANGE = (2000, 2020)

# API Endpoints
API_ENDPOINTS = {
    "world_bank": "https://api.worldbank.org/v2",
    "fao": "https://www.fao.org/faostat/api/v1/en"
}

def get_config():
    """
    Return a dictionary of configuration values.
    """
    return {
        "year_range": YEAR_RANGE,
        "api_endpoints": API_ENDPOINTS,
        "project_root": str(PROJECT_ROOT)
    }
