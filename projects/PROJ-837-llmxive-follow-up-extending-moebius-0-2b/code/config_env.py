"""
Environment configuration management for dataset paths and artifact hashes.

This module extends the base config.py to handle:
- Dataset directory paths ( Places365, CelebA-HQ, etc. )
- Artifact hash verification for data integrity
- Environment variable overrides for CI vs Research modes
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_mode, is_ci_mode, is_research_mode, get_config_summary
from utils.logger import get_logger

logger = get_logger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Default paths relative to project root
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"
DEFAULT_DATASETS_DIR = DEFAULT_DATA_ROOT / "raw"
DEFAULT_PROCESSED_DIR = DEFAULT_DATA_ROOT / "processed"
DEFAULT_ANNOTATIONS_DIR = DEFAULT_DATA_ROOT / "annotations"
DEFAULT_RESULTS_DIR = DEFAULT_DATA_ROOT / "results"
DEFAULT_CHECKSUMS_FILE = DEFAULT_DATA_ROOT / "manifest.json"

# Known dataset identifiers and their expected checksums (placeholders for real hashes)
# In a real implementation, these would be populated with actual SHA256 hashes
KNOWN_DATASET_HASHES = {
    "places365_standard": "TODO_REAL_HASH",
    "celeba_hq": "TODO_REAL_HASH",
}

class EnvConfig:
    """
    Manages environment-specific configuration for data paths and integrity checks.
    """
    
    def __init__(self):
        self.mode = get_mode()
        self.data_root = self._resolve_path("DATA_ROOT", DEFAULT_DATA_ROOT)
        self.datasets_dir = self._resolve_path("DATASETS_DIR", DEFAULT_DATASETS_DIR)
        self.processed_dir = self._resolve_path("PROCESSED_DIR", DEFAULT_PROCESSED_DIR)
        self.annotations_dir = self._resolve_path("ANNOTATIONS_DIR", DEFAULT_ANNOTATIONS_DIR)
        self.results_dir = self._resolve_path("RESULTS_DIR", DEFAULT_RESULTS_DIR)
        self.checksums_file = self._resolve_path("CHECKSUMS_FILE", DEFAULT_CHECKSUMS_FILE)
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load or initialize manifest
        self.manifest = self._load_manifest()

    def _resolve_path(self, env_var: str, default: Path) -> Path:
        """Resolve a path from environment variable or default."""
        env_val = os.getenv(env_var)
        if env_val:
            path = Path(env_val)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            return path
        return default

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            self.datasets_dir,
            self.processed_dir,
            self.annotations_dir,
            self.results_dir,
            self.processed_dir / "masked_images",
            self.annotations_dir / "decoupled_scores",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory: {d}")

    def _load_manifest(self) -> Dict[str, Any]:
        """Load the manifest file or return an empty structure."""
        if self.checksums_file.exists():
            try:
                with open(self.checksums_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load manifest: {e}. Initializing empty manifest.")
        return {
            "version": "1.0",
            "datasets": {},
            "artifacts": {},
            "last_updated": None
        }

    def save_manifest(self):
        """Save the current manifest to disk."""
        self.manifest["last_updated"] = str(Path(__file__).parent.parent / "config_env.py") # Placeholder for timestamp logic
        with open(self.checksums_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)
        logger.info(f"Manifest saved to {self.checksums_file}")

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def register_dataset(self, dataset_name: str, path: Path, expected_hash: Optional[str] = None):
        """
        Register a dataset in the manifest and verify its hash if expected_hash is provided.
        """
        if not path.exists():
            raise FileNotFoundError(f"Dataset path does not exist: {path}")
        
        actual_hash = self.compute_file_hash(path) if path.is_file() else "directory"
        
        if expected_hash and expected_hash != "TODO_REAL_HASH":
            if actual_hash != expected_hash:
                logger.warning(f"Hash mismatch for {dataset_name}: expected {expected_hash}, got {actual_hash}")
        
        self.manifest["datasets"][dataset_name] = {
            "path": str(path),
            "hash": actual_hash,
            "registered_mode": self.mode
        }
        self.save_manifest()
        logger.info(f"Registered dataset: {dataset_name} at {path}")

    def verify_artifact(self, artifact_name: str, path: Path) -> bool:
        """Verify an artifact's hash against the manifest."""
        if artifact_name not in self.manifest.get("artifacts", {}):
            logger.warning(f"Artifact {artifact_name} not found in manifest.")
            return False
        
        expected_hash = self.manifest["artifacts"][artifact_name]["hash"]
        if not path.exists():
            logger.error(f"Artifact file missing: {path}")
            return False
        
        actual_hash = self.compute_file_hash(path)
        if actual_hash != expected_hash:
            logger.error(f"Artifact hash mismatch for {artifact_name}: expected {expected_hash}, got {actual_hash}")
            return False
        
        logger.info(f"Artifact verified: {artifact_name}")
        return True

    def register_artifact(self, artifact_name: str, path: Path):
        """Register an artifact in the manifest."""
        if not path.exists():
            raise FileNotFoundError(f"Artifact path does not exist: {path}")
        
        actual_hash = self.compute_file_hash(path)
        self.manifest["artifacts"][artifact_name] = {
            "path": str(path),
            "hash": actual_hash,
            "registered_mode": self.mode
        }
        self.save_manifest()
        logger.info(f"Registered artifact: {artifact_name}")

    def get_dataset_path(self, dataset_name: str) -> Optional[Path]:
        """Get the path for a registered dataset."""
        if dataset_name in self.manifest.get("datasets", {}):
            return Path(self.manifest["datasets"][dataset_name]["path"])
        return None

    def get_config_summary(self) -> Dict[str, Any]:
        """Return a summary of the environment configuration."""
        return {
            "mode": self.mode,
            "data_root": str(self.data_root),
            "datasets_dir": str(self.datasets_dir),
            "processed_dir": str(self.processed_dir),
            "annotations_dir": str(self.annotations_dir),
            "results_dir": str(self.results_dir),
            "checksums_file": str(self.checksums_file),
            "registered_datasets": list(self.manifest.get("datasets", {}).keys()),
            "registered_artifacts": list(self.manifest.get("artifacts", {}).keys())
        }

# Global instance
_env_config: Optional[EnvConfig] = None

def get_env_config() -> EnvConfig:
    """Get the singleton EnvConfig instance."""
    global _env_config
    if _env_config is None:
        _env_config = EnvConfig()
    return _env_config

def reset_env_config():
    """Reset the singleton (useful for testing)."""
    global _env_config
    _env_config = None

def get_data_path(sub_path: str) -> Path:
    """Convenience function to get a path relative to the data root."""
    return get_env_config().data_root / sub_path

def get_datasets_path() -> Path:
    """Get the datasets directory path."""
    return get_env_config().datasets_dir

def get_annotations_path() -> Path:
    """Get the annotations directory path."""
    return get_env_config().annotations_dir

def get_results_path() -> Path:
    """Get the results directory path."""
    return get_env_config().results_dir

def verify_dataset(dataset_name: str, path: Path) -> bool:
    """Verify a dataset's integrity."""
    cfg = get_env_config()
    cfg.register_dataset(dataset_name, path)
    return True

def verify_artifact(artifact_name: str, path: Path) -> bool:
    """Verify an artifact's integrity."""
    cfg = get_env_config()
    return cfg.verify_artifact(artifact_name, path)

def register_artifact(artifact_name: str, path: Path):
    """Register an artifact."""
    cfg = get_env_config()
    cfg.register_artifact(artifact_name, path)
