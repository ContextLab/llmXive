import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_config():
    """Return a dictionary of configuration values."""
    return {
        "data_path": get_data_path(),
        "random_seed": get_random_seed(),
        "hypothetical_mode": os.getenv("HYPOTHETICAL_MODE", "false").lower() == "true"
    }

def get_data_path():
    """Return the path to the data directory."""
    return os.getenv("DATA_PATH", "data")

def get_random_seed():
    """Return the random seed."""
    return int(os.getenv("RANDOM_SEED", 42))

def validate_config():
    """Validate that required environment variables are set."""
    required = ["DATA_PATH", "RANDOM_SEED"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    return True
