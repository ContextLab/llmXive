import os
from typing import Optional

class Config:
    def __init__(self):
        self.npm_api_key: Optional[str] = os.getenv("NPM_API_KEY", "")
        self.github_token: Optional[str] = os.getenv("GITHUB_TOKEN", "")
        self.rate_limit: int = int(os.getenv("RATE_LIMIT", "60"))
        
        # Default paths
        self.data_raw_dir = "data/raw"
        self.data_processed_dir = "data/processed"

def get_config() -> Config:
    return Config()
