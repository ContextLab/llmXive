"""
Configuration loader for the project.
Defines API endpoints, year ranges, and data source identifiers.
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_OUTPUT_DIR = PROJECT_ROOT / "docs" / "output"

# API Configuration
API_ENDPOINTS = {
    'FAO_STAT': 'https://www.fao.org/faostat/api',
    'WORLD_BANK': 'https://api.worldbank.org/v2'
}

# Indicator Codes
FAO_INDICATOR = 'AG.LND.FRST.ZS'  # Forest Area Change
WB_CBNRM_INDICATOR = 'EG.GOV.POLI.ZS'  # Political Stability (CBNRM Proxy)
WB_GDP_INDICATOR = 'NY.GDP.PCAP.CD'  # GDP per capita
WB_POP_INDICATOR = 'SP.POP.TOTL'  # Total Population

# Year Range
YEAR_RANGE = {
    'START': 2000,
    'END': 2020
}

# Retry Configuration
RETRY_CONFIG = {
    'MAX_RETRIES': 3,
    'BACKOFF_FACTOR': 2,
    'TIMEOUT': 30
}

def get_config() -> dict:
    """
    Returns the complete configuration dictionary.
    
    Returns:
        dict: Configuration with API endpoints, indicators, and paths.
    """
    return {
        'API_BASE_URL': API_ENDPOINTS['FAO_STAT'],
        'DATA_YEARS_START': YEAR_RANGE['START'],
        'DATA_YEARS_END': YEAR_RANGE['END'],
        'FAO_INDICATOR': FAO_INDICATOR,
        'WB_CBNRM_INDICATOR': WB_CBNRM_INDICATOR,
        'WB_GDP_INDICATOR': WB_GDP_INDICATOR,
        'WB_POP_INDICATOR': WB_POP_INDICATOR,
        'DATA_RAW_DIR': str(DATA_RAW_DIR),
        'DATA_PROCESSED_DIR': str(DATA_PROCESSED_DIR),
        'DOCS_OUTPUT_DIR': str(DOCS_OUTPUT_DIR),
        'RETRY_CONFIG': RETRY_CONFIG
    }