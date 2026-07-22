"""
Configuration settings for the Coating Adhesion Pipeline.
"""
import os

# API Keys and URLs (These should be set via environment variables in production)
MP_API_KEY = os.getenv('MP_API_KEY', 'default_mp_key')
NIST_URL = os.getenv('NIST_URL', 'https://nist.gov/surface-metrology')
LIT_API_URL = os.getenv('LIT_API_URL', '')
LIT_API_KEY = os.getenv('LIT_API_KEY', '')

# Thresholds
PROXY_CORR_THRESHOLD = float(os.getenv('PROXY_CORR_THRESHOLD', '0.3'))
PROXY_R2_THRESHOLD = float(os.getenv('PROXY_R2_THRESHOLD', '0.6'))

# Limits
MAX_ROWS = int(os.getenv('MAX_ROWS', '5000'))
RAM_LIMIT_GB = float(os.getenv('RAM_LIMIT_GB', '7'))
TIMEOUT_HOURS = int(os.getenv('TIMEOUT_HOURS', '4'))

# Directories
DATA_RAW_DIR = os.getenv('DATA_RAW_DIR', 'data/raw')
DATA_PROCESSED_DIR = os.getenv('DATA_PROCESSED_DIR', 'data/processed')
STATE_DIR = os.getenv('STATE_DIR', 'state')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Sensitivity Analysis Definitions
# List of ratio definitions for crosslinker density proxy
CROSSLINKER_PROXY_DEFINITIONS = [
    "crosslinker_fraction",
    "crosslinker_matrix_ratio",
    "crosslinker_fraction_squared"
]

def main():
    """Print configuration."""
    print(f"MP_API_KEY: {MP_API_KEY}")
    print(f"NIST_URL: {NIST_URL}")
    print(f"MAX_ROWS: {MAX_ROWS}")
    print(f"RAM_LIMIT_GB: {RAM_LIMIT_GB}")
    print(f"CROSSLINKER_PROXY_DEFINITIONS: {CROSSLINKER_PROXY_DEFINITIONS}")

if __name__ == '__main__':
    main()
