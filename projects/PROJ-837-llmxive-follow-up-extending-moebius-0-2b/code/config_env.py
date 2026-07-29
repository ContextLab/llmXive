import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_mode, is_ci_mode, is_research_mode, get_config_summary

class EnvConfig:
    """Environment configuration container."""
    def __init__(
        self,
        data_root: Path,
        datasets_path: Path,
        annotations_path: Path,
        results_path: Path,
        artifacts_manifest: Path
    ):
        self.data_root = data_root
        self.datasets_path = datasets_path
        self.annotations_path = annotations_path
        self.results_path = results_path
        self.artifacts_manifest = artifacts_manifest

        # Ensure directories exist
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.datasets_path.mkdir(parents=True, exist_ok=True)
        self.annotations_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.artifacts_manifest.parent.mkdir(parents=True, exist_ok=True)

_env_config: Optional[EnvConfig] = None

def get_env_config() -> EnvConfig:
    """Get or initialize the environment configuration."""
    global _env_config
    if _env_config is None:
        project_root = Path(__file__).parent.parent
        _env_config = EnvConfig(
            data_root=project_root / "data",
            datasets_path=project_root / "data" / "datasets",
            annotations_path=project_root / "data" / "annotations",
            results_path=project_root / "data" / "results",
            artifacts_manifest=project_root / "data" / "artifacts_manifest.json"
        )
    return _env_config

def reset_env_config() -> None:
    """Reset the environment configuration (useful for testing)."""
    global _env_config
    _env_config = None

def get_data_path() -> Path:
    """Get the root data path."""
    return get_env_config().data_root

def get_datasets_path() -> Path:
    """Get the datasets directory path."""
    return get_env_config().datasets_path

def get_annotations_path() -> Path:
    """Get the annotations directory path."""
    return get_env_config().annotations_path

def get_results_path() -> Path:
    """Get the results directory path."""
    return get_env_config().results_path

def verify_dataset(dataset_id: str, expected_hash: Optional[str] = None) -> bool:
    """
    Verify a dataset exists and optionally check its hash.
    Returns True if valid, False otherwise.
    """
    dataset_dir = get_datasets_path() / dataset_id
    if not dataset_dir.exists():
        return False

    if expected_hash:
        # Simple recursive hash of directory content
        hasher = hashlib.sha256()
        for file_path in sorted(dataset_dir.rglob("*")):
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
        actual_hash = hasher.hexdigest()
        return actual_hash == expected_hash

    return True

def verify_artifact(artifact_name: str) -> bool:
    """Check if an artifact is registered in the manifest."""
    manifest_path = get_env_config().artifacts_manifest
    if not manifest_path.exists():
        return False

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    return artifact_name in manifest

def register_artifact(artifact_name: str, path: Path, hash_val: str) -> None:
    """Register an artifact in the manifest."""
    manifest_path = get_env_config().artifacts_manifest
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

    manifest[artifact_name] = {
        "path": str(path),
        "hash": hash_val,
        "mode": get_mode()
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
