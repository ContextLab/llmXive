import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Set
import pandas as pd
from config import get_data_dir, get_output_dir, ensure_directories

DATA_STATE_FILE = "data_state.json"

def fetch_defects4j_data() -> pd.DataFrame:
    """
    Fetch Defects4J parquet data from HuggingFace and cache locally.
    Returns the loaded DataFrame.
    """
    ensure_directories()
    data_dir = get_data_dir()
    cache_path = data_dir / "defects4j_v1.0.parquet"
    
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    
    # Real source: HuggingFace dataset repository
    try:
        from datasets import load_dataset
        dataset = load_dataset("defects4j/defects4j-parquet", "v1.0", split="train")
        df = dataset.to_pandas()
        df.to_parquet(cache_path, index=False)
        return df
    except ImportError:
        raise ImportError("Please install 'datasets' package: pip install datasets")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Defects4J data: {e}")

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the project state from data_state.json.
    Returns empty dict if file doesn't exist.
    """
    state_path = Path(DATA_STATE_FILE)
    if state_path.exists():
        with open(state_path, "r") as f:
            return json.load(f)
    return {}

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to data_state.json.
    """
    with open(DATA_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def record_checksum(file_path: Path) -> None:
    """
    Compute SHA-256 hash of the given file and store it in the project state.
    Satisfies Constitution Principle III by recording data integrity.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot compute checksum: {file_path} does not exist")
    
    checksum = compute_sha256(file_path)
    state = load_state()
    
    if "checksums" not in state:
        state["checksums"] = {}
    
    state["checksums"][file_path.name] = {
        "algorithm": "sha256",
        "hash": checksum,
        "recorded_at": str(pd.Timestamp.now())
    }
    
    save_state(state)

def load_defects4j_data() -> pd.DataFrame:
    """
    Load Defects4J data from cache. Fetches if not present.
    """
    return fetch_defects4j_data()

def verify_data_integrity(file_path: Path) -> bool:
    """
    Verify the integrity of a cached file against its recorded checksum.
    Returns True if valid, False otherwise.
    """
    if not file_path.exists():
        return False
    
    state = load_state()
    if "checksums" not in state:
        return False
    
    recorded = state["checksums"].get(file_path.name)
    if not recorded or recorded.get("algorithm") != "sha256":
        return False
    
    current_hash = compute_sha256(file_path)
    return current_hash == recorded["hash"]

def ensure_data_loaded_and_integrity_recorded() -> pd.DataFrame:
    """
    Main entry point to ensure data is loaded and its checksum is recorded.
    Returns the DataFrame.
    """
    data_dir = get_data_dir()
    ensure_directories()
    cache_path = data_dir / "defects4j_v1.0.parquet"
    
    # Fetch data if not present
    if not cache_path.exists():
        fetch_defects4j_data()
    
    # Record checksum if not already recorded
    state = load_state()
    if "checksums" not in state or cache_path.name not in state["checksums"]:
        record_checksum(cache_path)
    
    return pd.read_parquet(cache_path)

def extract_changed_lines(df: pd.DataFrame) -> Set[int]:
    """
    Placeholder for T025: Extract changed lines from commit diffs.
    Currently returns an empty set.
    """
    # This will be implemented in T025
    return set()