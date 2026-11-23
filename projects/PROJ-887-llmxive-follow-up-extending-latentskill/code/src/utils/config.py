import os
import sys
import random
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_data_path(subpath: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Returns the data directory root, or a subpath within it.
    Handles multiple call signatures:
    1. get_data_path() -> returns data directory root
    2. get_data_path("raw") -> returns data/raw
    3. get_data_path(project_root=Path(...)) -> returns data dir for that root
    4. get_data_path("raw", project_root=Path(...)) -> returns data/raw for that root
    """
    root = project_root if project_root else get_project_root()
    base = root / "data"
    if subpath:
        return base / subpath
    return base

def get_artifacts_path(subpath: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    root = project_root if project_root else get_project_root()
    base = root / "artifacts"
    if subpath:
        return base / subpath
    return base

def get_results_path(subpath: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    root = project_root if project_root else get_project_root()
    base = root / "data" / "results"
    if subpath:
        return base / subpath
    return base

def ensure_directories(paths: Optional[Union[Path, List[Path], List[str]]] = None) -> None:
    """
    Creates directories for the given paths.
    Handles multiple call signatures:
    1. ensure_directories() -> does nothing (graceful no-op)
    2. ensure_directories(Path(...)) -> creates that directory
    3. ensure_directories([Path(...), ...]) -> creates all directories
    4. ensure_directories([str, ...]) -> creates all directories
    """
    if paths is None:
        return

    if isinstance(paths, (Path, str)):
        paths = [paths]

    for p in paths:
        if isinstance(p, str):
            p = Path(p)
        p.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)

def load_config(config_path: Path) -> Dict[str, Any]:
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
