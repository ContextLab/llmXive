import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class Config:
    WINDOW_SIZES: List[int]
    STEP: int
    ATLAS_PATH: Path
    DATA_PATH: Path

def get_config() -> Config:
    """
    Load configuration from environment variables or use defaults.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    
    window_sizes = [20, 30, 40]
    step = 5
    
    # Allow override via environment variables
    if "WINDOW_SIZES" in os.environ:
        try:
            window_sizes = [int(x) for x in os.environ["WINDOW_SIZES"].split(",")]
        except ValueError:
            pass
    
    if "STEP" in os.environ:
        try:
            step = int(os.environ["STEP"])
        except ValueError:
            pass
    
    atlas_path = project_root / "data" / "atlas" / "default_atlas.nii.gz"
    data_path = project_root / "data" / "raw"
    
    if "ATLAS_PATH" in os.environ:
        atlas_path = Path(os.environ["ATLAS_PATH"])
    
    if "DATA_PATH" in os.environ:
        data_path = Path(os.environ["DATA_PATH"])
    
    return Config(
        WINDOW_SIZES=window_sizes,
        STEP=step,
        ATLAS_PATH=atlas_path,
        DATA_PATH=data_path
    )
