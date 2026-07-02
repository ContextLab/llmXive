import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Project Paths
DATA_RAW_PATH = 'data/raw'
DATA_PROCESSED_PATH = 'data/processed'
DATA_INTERIM_PATH = 'data/interim'
DATA_ARTIFACTS_PATH = 'data/artifacts'
ARTIFACTS_PATH = DATA_ARTIFACTS_PATH

# Configuration Constants
SEED = 42
MAX_RUNTIME_HOURS = 4

# External API Base URLs
NCBI_BASE_URL = os.getenv('NCBI_BASE_URL', 'https://www.ncbi.nlm.nih.gov/nuccore')
GEO_BASE_URL = 'https://www.ncbi.nlm.nih.gov/geo/download'

# Environment Variables (Optional, defaulting to None if missing)
NCBI_API_KEY = os.getenv('NCBI_API_KEY', None)
GEO_ACCESSIONS = os.getenv('GEO_ACCESSIONS', None)