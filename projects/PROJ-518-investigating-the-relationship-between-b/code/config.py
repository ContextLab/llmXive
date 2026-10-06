import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class Config:
    WINDOW_SIZES: List[int] = None
    STEP: int = 5
    ATLAS_PATH: Optional[str] = None
    DATA_PATH: Optional[str] = None
    FWE_METHOD: str = 'max-t'

    def __post_init__(self):
        if self.WINDOW_SIZES is None:
            self.WINDOW_SIZES = [20, 30, 40]

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
        # Load from environment variables if present
        if os.path.exists('.env'):
            from dotenv import load_dotenv
            load_dotenv()
        
        if 'WINDOW_SIZES' in os.environ:
            _config.WINDOW_SIZES = [int(x) for x in os.environ['WINDOW_SIZES'].split(',')]
        if 'STEP' in os.environ:
            _config.STEP = int(os.environ['STEP'])
        if 'ATLAS_PATH' in os.environ:
            _config.ATLAS_PATH = os.environ['ATLAS_PATH']
        if 'DATA_PATH' in os.environ:
            _config.DATA_PATH = os.environ['DATA_PATH']
        if 'FWE_METHOD' in os.environ:
            _config.FWE_METHOD = os.environ['FWE_METHOD']
    
    return _config