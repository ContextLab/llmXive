"""
I/O Utilities for robust file handling.
"""
import csv
import json
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

class IOLoadError(Exception):
    """Exception raised when a file cannot be loaded."""
    pass

class IOSaveError(Exception):
    """Exception raised when a file cannot be saved."""
    pass

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure the directory for the given path exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def file_exists(path: Union[str, Path]) -> bool:
    """Check if a file exists."""
    return Path(path).exists()

def load_csv(path: Union[str, Path], **kwargs) -> Any:
    """Load a CSV file into a list of dicts or pandas DataFrame."""
    try:
        import pandas as pd
        return pd.read_csv(path, **kwargs)
    except Exception as e:
        raise IOLoadError(f"Failed to load CSV {path}: {e}")

def save_csv(data: Union[List[Dict], Any], path: Union[str, Path], **kwargs) -> None:
    """Save data to a CSV file."""
    try:
        import pandas as pd
        if isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            df.to_csv(path, index=False, **kwargs)
        else:
            # Assume it's already a DataFrame or similar
            data.to_csv(path, index=False, **kwargs)
    except Exception as e:
        raise IOSaveError(f"Failed to save CSV {path}: {e}")

def load_json(path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise IOLoadError(f"Failed to load JSON {path}: {e}")

def save_json(data: Any, path: Union[str, Path], **kwargs) -> None:
    """Save data to a JSON file."""
    try:
        ensure_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, **kwargs)
    except Exception as e:
        raise IOSaveError(f"Failed to save JSON {path}: {e}")

def load_yaml(path: Union[str, Path]) -> Any:
    """Load a YAML file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise IOLoadError(f"Failed to load YAML {path}: {e}")

def save_yaml(data: Any, path: Union[str, Path], **kwargs) -> None:
    """Save data to a YAML file."""
    try:
        ensure_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, **kwargs)
    except Exception as e:
        raise IOSaveError(f"Failed to save YAML {path}: {e}")

def load_jsonl(path: Union[str, Path]) -> List[Dict]:
    """Load a JSONL file."""
    try:
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    except Exception as e:
        raise IOLoadError(f"Failed to load JSONL {path}: {e}")

def save_jsonl(data: List[Dict], path: Union[str, Path]) -> None:
    """Save a list of dicts to a JSONL file."""
    try:
        ensure_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
    except Exception as e:
        raise IOSaveError(f"Failed to save JSONL {path}: {e}")
