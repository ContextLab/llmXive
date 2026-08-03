import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_mode, is_ci_mode, is_research_mode, get_config_summary

class EnvConfig:
    """Environment configuration container for dataset paths and artifact hashes."""
    
    def __init__(
        self,
        root: str,
        datasets_dir: Optional[str] = None,
        annotations_dir: Optional[str] = None,
        results_dir: Optional[str] = None,
        artifact_hashes: Optional[Dict[str, str]] = None
    ):
        self.root = Path(root).resolve()
        self.datasets_dir = Path(datasets_dir) if datasets_dir else self.root / "data" / "datasets"
        self.annotations_dir = Path(annotations_dir) if annotations_dir else self.root / "data" / "annotations"
        self.results_dir = Path(results_dir) if results_dir else self.root / "data" / "results"
        self.artifact_hashes = artifact_hashes or {}
        self._hash_file = self.root / "data" / ".artifact_hashes.json"
        
    def ensure_dirs(self) -> None:
        """Create all required directories if they don't exist."""
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.annotations_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._hash_file.parent.mkdir(parents=True, exist_ok=True)
        
    def save_hashes(self) -> None:
        """Persist artifact hashes to disk."""
        with open(self._hash_file, 'w') as f:
            json.dump(self.artifact_hashes, f, indent=2)
            
    def load_hashes(self) -> None:
        """Load artifact hashes from disk if they exist."""
        if self._hash_file.exists():
            with open(self._hash_file, 'r') as f:
                self.artifact_hashes = json.load(f)
                
    def register_artifact(self, name: str, path: str, compute_hash: bool = True) -> str:
        """Register an artifact path and compute/store its hash."""
        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = self.root / path
            
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {full_path}")
            
        if compute_hash:
            file_hash = self._compute_file_hash(full_path)
            self.artifact_hashes[name] = file_hash
            self.save_hashes()
            return file_hash
        return ""
        
    def verify_artifact(self, name: str, expected_hash: Optional[str] = None) -> bool:
        """Verify an artifact exists and matches its registered hash."""
        if name not in self.artifact_hashes:
            return False
            
        registered_hash = self.artifact_hashes[name]
        full_path = self.root / name if not Path(name).is_absolute() else Path(name)
        
        if not full_path.exists():
            return False
            
        if expected_hash:
            return self._compute_file_hash(full_path) == expected_hash
        return self._compute_file_hash(full_path) == registered_hash
        
    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

# Global configuration instance
_env_config: Optional[EnvConfig] = None

def get_env_config() -> EnvConfig:
    """Get or create the global environment configuration."""
    global _env_config
    if _env_config is None:
        root = os.getenv("LLMXIVE_ROOT", ".")
        _env_config = EnvConfig(root)
        _env_config.load_hashes()
    return _env_config

def reset_env_config() -> None:
    """Reset the global environment configuration (useful for testing)."""
    global _env_config
    _env_config = None

def get_data_path() -> Path:
    """Get the root data directory."""
    return get_env_config().root / "data"

def get_datasets_path() -> Path:
    """Get the datasets directory."""
    return get_env_config().datasets_dir

def get_annotations_path() -> Path:
    """Get the annotations directory."""
    return get_env_config().annotations_dir

def get_results_path() -> Path:
    """Get the results directory."""
    return get_env_config().results_dir

def verify_dataset(name: str, expected_hash: Optional[str] = None) -> bool:
    """Verify a dataset exists and matches its registered hash."""
    return get_env_config().verify_artifact(name, expected_hash)

def register_artifact(name: str, path: str, compute_hash: bool = True) -> str:
    """Register an artifact and compute/store its hash."""
    return get_env_config().register_artifact(name, path, compute_hash)

def ensure_env_paths_exist() -> None:
    """Ensure all environment paths exist."""
    get_env_config().ensure_dirs()

def get_env_config_summary() -> Dict[str, Any]:
    """Get a summary of the environment configuration."""
    cfg = get_env_config()
    return {
        "root": str(cfg.root),
        "datasets_dir": str(cfg.datasets_dir),
        "annotations_dir": str(cfg.annotations_dir),
        "results_dir": str(cfg.results_dir),
        "registered_artifacts": list(cfg.artifact_hashes.keys()),
        "mode": get_mode()
    }
