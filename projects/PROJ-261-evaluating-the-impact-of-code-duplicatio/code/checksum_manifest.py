import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging for checksum manifest operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/checksum_manifest.log')
        ]
    )

def compute_file_checksum(file_path: str | Path, algorithm: str = 'sha256') -> str:
    """Compute SHA-256 checksum of a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        sha256_hash = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        raise

def compute_all_artifact_checksums(artifact_paths: List[str | Path], algorithm: str = 'sha256') -> Dict[str, str]:
    """Compute checksums for all artifact files."""
    checksums = {}
    for path in artifact_paths:
        try:
            checksums[str(path)] = compute_file_checksum(path, algorithm)
        except Exception as e:
            logger.warning(f"Skipping {path}: {e}")
    return checksums

def load_manifest(manifest_path: str | Path) -> Dict[str, Any]:
    """Load manifest from JSON file."""
    path = Path(manifest_path)
    if not path.exists():
        logger.warning(f"Manifest not found at {manifest_path}, creating new one")
        return {"version": "1.0", "created": datetime.now().isoformat(), "artifacts": {}}
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse manifest JSON: {e}")
        raise

def save_manifest(manifest_path: str | Path, manifest: Dict[str, Any]) -> None:
    """Save manifest to JSON file."""
    # FIX: Ensure manifest_path is a Path object, not a dict
    if isinstance(manifest_path, dict):
        logger.error(f"manifest_path is dict, not Path: {manifest_path}")
        raise TypeError(f"manifest_path must be Path or str, got {type(manifest_path)}")
    
    path = Path(manifest_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
        logger.info(f"Saved manifest to {path}")
    except Exception as e:
        logger.error(f"Failed to save manifest to {manifest_path}: {e}")
        raise

def record_artifact_checksums(manifest_path: str | Path, artifact_paths: List[str | Path], algorithm: str = 'sha256') -> Dict[str, Any]:
    """Record checksums for artifacts in manifest."""
    manifest = load_manifest(manifest_path)
    checksums = compute_all_artifact_checksums(artifact_paths, algorithm)
    
    for path_str, checksum in checksums.items():
        manifest["artifacts"][path_str] = {
            "checksum": checksum,
            "algorithm": algorithm,
            "recorded_at": datetime.now().isoformat()
        }
    
    save_manifest(manifest_path, manifest)
    return manifest

def verify_artifact_checksums(manifest_path: str | Path, algorithm: str = 'sha256') -> Dict[str, bool]:
    """Verify all artifact checksums against manifest."""
    manifest = load_manifest(manifest_path)
    results = {}
    
    for path_str, artifact_info in manifest.get("artifacts", {}).items():
        try:
            current_checksum = compute_file_checksum(path_str, algorithm)
            expected_checksum = artifact_info.get("checksum")
            results[path_str] = current_checksum == expected_checksum
        except Exception as e:
            logger.error(f"Failed to verify {path_str}: {e}")
            results[path_str] = False
    
    return results

def get_artifact_hashes(manifest_path: str | Path) -> Dict[str, str]:
    """Extract artifact hashes from manifest for checksum tracking."""
    manifest = load_manifest(manifest_path)
    return {
        path: info.get("checksum", "")
        for path, info in manifest.get("artifacts", {}).items()
    }

def add_custom_artifact(manifest_path: str | Path, artifact_path: str | Path, checksum: str, algorithm: str = 'sha256') -> None:
    """Add a custom artifact to the manifest."""
    manifest = load_manifest(manifest_path)
    path_str = str(Path(artifact_path))
    
    manifest["artifacts"][path_str] = {
        "checksum": checksum,
        "algorithm": algorithm,
        "recorded_at": datetime.now().isoformat()
    }
    
    save_manifest(manifest_path, manifest)

def main():
    """Main entry point for checksum manifest operations."""
    setup_logging()
    manifest_path = Path("data/checksum_manifest.json")
    
    # Record checksums for key artifacts
    artifacts = [
        "data/processed/clone_metrics.csv",
        "data/processed/perplexity_scores.csv",
        "data/analysis/correlation_results.csv",
        "data/parse_failures.csv",
        "data/raw/github-code-sample.csv"
    ]
    
    try:
        manifest = record_artifact_checksums(manifest_path, artifacts)
        print(f"Manifest updated with {len(manifest['artifacts'])} artifacts")
    except Exception as e:
        logger.error(f"Failed to record checksums: {e}")
        raise

if __name__ == "__main__":
    main()
