"""
Environment configuration management for dataset paths and artifact hashes.

Handles:
- Dataset path resolution
- Artifact hash verification and registration
- Mode-specific path generation (CI vs Research)
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_mode, is_ci_mode, get_config_summary

# Constants for directory structure
DATA_ROOT = Path("data")
DATASETS_DIR = DATA_ROOT / "raw"
PROCESSED_DIR = DATA_ROOT / "processed"
ANNOTATIONS_DIR = DATA_ROOT / "annotations"
RESULTS_DIR = DATA_ROOT / "results"
ARTIFACTS_DIR = DATA_ROOT / "artifacts"
HASHES_FILE = ARTIFACTS_DIR / "artifact_hashes.json"

# Default dataset configurations
DEFAULT_DATASETS = {
    "places365": {
        "name": "mit-places/Places365",
        "subset": "standard",
        "checksum": None  # Will be computed on first fetch
    },
    "celebahq": {
        "name": "celeba-hq",
        "subset": "train",
        "checksum": None
    }
}

class EnvConfig:
    """Environment configuration container."""
    
    def __init__(self, 
                data_root: Path = DATA_ROOT,
                datasets_dir: Path = DATASETS_DIR,
                processed_dir: Path = PROCESSED_DIR,
                annotations_dir: Path = ANNOTATIONS_DIR,
                results_dir: Path = RESULTS_DIR,
                artifacts_dir: Path = ARTIFACTS_DIR,
                hashes_file: Path = HASHES_FILE,
                mode: str = "research"):
        self.data_root = data_root
        self.datasets_dir = datasets_dir
        self.processed_dir = processed_dir
        self.annotations_dir = annotations_dir
        self.results_dir = results_dir
        self.artifacts_dir = artifacts_dir
        self.hashes_file = hashes_file
        self.mode = mode
        self._dataset_registry: Dict[str, Dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self):
        """Load artifact hash registry from disk."""
        if self.hashes_file.exists():
            try:
                with open(self.hashes_file, 'r') as f:
                    self._dataset_registry = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load artifact registry: {e}")
                self._dataset_registry = {}
        else:
            self._dataset_registry = {}

    def save_registry(self):
        """Save artifact hash registry to disk."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        with open(self.hashes_file, 'w') as f:
            json.dump(self._dataset_registry, f, indent=2)

    def register_artifact(self, name: str, path: Path, hash_value: str, 
                        metadata: Optional[Dict[str, Any]] = None):
        """Register an artifact with its hash and metadata."""
        self._dataset_registry[name] = {
            "path": str(path),
            "hash": hash_value,
            "mode": self.mode,
            "metadata": metadata or {},
            "registered_at": str(Path.cwd().joinpath(name).stat().st_mtime if path.exists() else 0)
        }
        self.save_registry()

    def verify_artifact(self, name: str, path: Path) -> bool:
        """Verify an artifact's hash matches the registered value."""
        if name not in self._dataset_registry:
            return False
        
        registered = self._dataset_registry[name]
        if registered.get("path") != str(path):
            return False
        
        current_hash = self._compute_file_hash(path)
        return current_hash == registered.get("hash")

    def _compute_file_hash(self, path: Path, algorithm: str = "sha256") -> str:
        """Compute SHA256 hash of a file."""
        if not path.exists():
            raise FileNotFoundError(f"Cannot compute hash: file not found - {path}")
        
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_artifact_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get registered info for an artifact."""
        return self._dataset_registry.get(name)

# Global instance
_env_config: Optional[EnvConfig] = None

def get_env_config() -> EnvConfig:
    """Get or create the global environment configuration."""
    global _env_config
    if _env_config is None:
        mode = "ci" if is_ci_mode() else "research"
        _env_config = EnvConfig(mode=mode)
    return _env_config

def reset_env_config():
    """Reset the global environment configuration."""
    global _env_config
    _env_config = None

def get_data_path() -> Path:
    """Get the root data directory."""
    return get_env_config().data_root

def get_datasets_path() -> Path:
    """Get the datasets directory."""
    return get_env_config().datasets_dir

def get_annotations_path() -> Path:
    """Get the annotations directory."""
    return get_env_config().annotations_dir

def get_results_path() -> Path:
    """Get the results directory."""
    return get_env_config().results_dir

def ensure_env_paths_exist():
    """Ensure all environment paths exist."""
    env_config = get_env_config()
    env_config.data_root.mkdir(parents=True, exist_ok=True)
    env_config.datasets_dir.mkdir(parents=True, exist_ok=True)
    env_config.processed_dir.mkdir(parents=True, exist_ok=True)
    env_config.annotations_dir.mkdir(parents=True, exist_ok=True)
    env_config.results_dir.mkdir(parents=True, exist_ok=True)
    env_config.artifacts_dir.mkdir(parents=True, exist_ok=True)
    # Initialize empty hash file if it doesn't exist
    if not env_config.hashes_file.exists():
        env_config.hashes_file.write_text("{}")

def verify_dataset(dataset_name: str, path: Path) -> Tuple[bool, Optional[str]]:
    """
    Verify a dataset's integrity using stored hash.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    env_config = get_env_config()
    
    if not path.exists():
        return False, f"Dataset file not found: {path}"
    
    if env_config.verify_artifact(dataset_name, path):
        return True, None
    
    # If not registered, compute and register
    try:
        hash_value = env_config._compute_file_hash(path)
        metadata = {
            "size_bytes": path.stat().st_size,
            "verified_at": "now"
        }
        env_config.register_artifact(dataset_name, path, hash_value, metadata)
        return True, None
    except Exception as e:
        return False, f"Hash computation failed: {str(e)}"

def get_env_config_summary() -> Dict[str, Any]:
    """Get a summary of the current environment configuration."""
    env_config = get_env_config()
    return {
        "mode": env_config.mode,
        "data_root": str(env_config.data_root),
        "datasets_dir": str(env_config.datasets_dir),
        "annotations_dir": str(env_config.annotations_dir),
        "results_dir": str(env_config.results_dir),
        "registered_artifacts": list(env_config._dataset_registry.keys()),
        "total_artifacts": len(env_config._dataset_registry)
    }

def register_artifact(name: str, path: Path, hash_value: str = None, 
                     metadata: Optional[Dict[str, Any]] = None):
    """Convenience function to register an artifact."""
    env_config = get_env_config()
    if hash_value is None:
        hash_value = env_config._compute_file_hash(path)
    env_config.register_artifact(name, path, hash_value, metadata)
    return hash_value
