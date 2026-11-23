import os
import sys
import random
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_data_path(subdir: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Returns the data directory path.
    
    Handles multiple call signatures:
    1. get_data_path() -> returns data dir root
    2. get_data_path("raw") -> returns data/raw
    3. get_data_path(project_root=Path(...)) -> returns data dir for that root
    4. get_data_path("raw", project_root=Path(...)) -> returns data/raw for that root
    """
    root = project_root if project_root else get_project_root()
    data_dir = root / "data"
    
    if subdir:
        return data_dir / subdir
    return data_dir

def get_artifacts_path(subdir: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """Returns the artifacts directory path."""
    root = project_root if project_root else get_project_root()
    artifacts_dir = root / "artifacts"
    if subdir:
        return artifacts_dir / subdir
    return artifacts_dir

def get_results_path(subdir: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """Returns the results directory path."""
    root = project_root if project_root else get_project_root()
    results_dir = root / "data" / "results"
    if subdir:
        return results_dir / subdir
    return results_dir

def ensure_directories(paths: Optional[Union[List[Path], Path]] = None) -> None:
    """
    Ensures the provided directory paths exist.
    
    Handles multiple call signatures:
    1. ensure_directories([Path(...)]) -> creates list of dirs
    2. ensure_directories() -> does nothing (no-op)
    3. ensure_directories(Path(...)) -> creates single dir
    """
    if paths is None:
        return
    
    if not isinstance(paths, list):
        paths = [paths]
    
    for p in paths:
        if isinstance(p, Path):
            p.mkdir(parents=True, exist_ok=True)
        else:
            # Handle string paths if passed
            Path(p).mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42) -> None:
    """Sets random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def load_config(config_path: Path) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)