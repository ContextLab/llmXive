import os
import json
from typing import Dict, Any, Optional

def get_config() -> Dict[str, Any]:
    """
    Loads the configuration from a JSON file or returns defaults.
    Expects a 'config.json' in the project root or environment variables.
    """
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    
    # Default config with a placeholder for research verified datasets
    # In a real scenario, this should be populated from research.md or a real source
    return {
        "research": {
            "verified_datasets": {
                "hea_compositions": "https://raw.githubusercontent.com/HEA-dataset/main/data/hea_compositions.csv"
            }
        }
    }

def get_verified_dataset_url() -> Optional[str]:
    """
    Retrieves the verified dataset URL for HEA compositions.
    
    Returns:
        The URL string or None if not found.
    """
    config = get_config()
    try:
        return config['research']['verified_datasets']['hea_compositions']
    except KeyError:
        return None

def ensure_dataset_url_exists() -> str:
    """
    Ensures the dataset URL exists in config. If not, raises an error.
    """
    url = get_verified_dataset_url()
    if not url:
        raise RuntimeError("DATA_SOURCE_MISSING: Verified dataset URL not found.")
    return url

def main():
    print("Config loaded.")

if __name__ == "__main__":
    main()
