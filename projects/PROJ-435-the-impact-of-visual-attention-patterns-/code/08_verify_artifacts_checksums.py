import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import logging setup from the project's established utils
# Note: We use the specific logger setup pattern found in utils/logging_init.py
# but for a standalone verification script, we can initialize a basic logger 
# or rely on the global one if T008b has run. 
# To be safe and self-contained, we initialize a basic logger here.
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger("checksum_verification")

def get_project_root() -> Path:
    """Returns the root directory of the project (parent of 'code')."""
    current_file = Path(__file__).resolve()
    # Assuming the script is at code/08_verify_artifacts_checksums.py
    return current_file.parent.parent

def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise

def load_hash_registry(state_path: Path) -> Dict[str, Any]:
    """Loads the existing hash registry from state/data_hashes.json."""
    if not state_path.exists():
        logger.warning(f"Hash registry not found at {state_path}. Creating new registry.")
        return {}
    
    with open(state_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in hash registry: {state_path}")
            return {}

def save_hash_registry(state_path: Path, registry: Dict[str, Any]) -> None:
    """Saves the updated hash registry to state/data_hashes.json."""
    with open(state_path, "w") as f:
        json.dump(registry, f, indent=2)
    logger.info(f"Hash registry saved to {state_path}")

def verify_artifact(file_path: Path, registry: Dict[str, Any]) -> bool:
    """Verifies a single artifact against the registry or adds it if missing."""
    rel_path = str(file_path.relative_to(get_project_root()))
    current_hash = compute_sha256(file_path)
    
    if rel_path in registry:
        if registry[rel_path] == current_hash:
            logger.debug(f"Verified: {rel_path} (hash matches)")
            return True
        else:
            logger.warning(f"Mismatch detected: {rel_path}")
            logger.warning(f"  Expected: {registry[rel_path]}")
            logger.warning(f"  Found:    {current_hash}")
            return False
    else:
        logger.info(f"New artifact detected: {rel_path}")
        return True

def scan_artifacts(project_root: Path) -> List[Path]:
    """Scans the project for all generated artifacts in data/, output/, state/, figures/."""
    artifact_dirs = ['data', 'output', 'state', 'figures']
    artifacts = []
    
    for dir_name in artifact_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    # Exclude the registry file itself from the scan to avoid circular issues,
                    # though it will be updated at the end.
                    if file_path.name != 'data_hashes.json':
                        artifacts.append(file_path)
    
    return sorted(artifacts)

def main():
    project_root = get_project_root()
    state_dir = project_root / "state"
    registry_path = state_dir / "data_hashes.json"
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting artifact verification for project: {project_root}")
    
    # Load existing registry
    registry = load_hash_registry(registry_path)
    
    # Scan for artifacts
    artifacts = scan_artifacts(project_root)
    
    if not artifacts:
        logger.warning("No artifacts found in data/, output/, state/, or figures/ directories.")
        # Even if empty, we save the registry (which might be empty or contain old entries)
        save_hash_registry(registry_path, registry)
        return

    all_verified = True
    updated_registry = registry.copy()

    for artifact in artifacts:
        try:
            if verify_artifact(artifact, registry):
                rel_path = str(artifact.relative_to(project_root))
                current_hash = compute_sha256(artifact)
                updated_registry[rel_path] = current_hash
            else:
                all_verified = False
        except Exception as e:
            logger.error(f"Failed to verify {artifact}: {e}")
            all_verified = False

    # Save the updated registry
    save_hash_registry(registry_path, updated_registry)

    if all_verified:
        logger.info("Verification complete. All artifacts are checksummed and valid.")
        # Write a summary report to output
        report_path = project_root / "output" / "verification_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump({
                "status": "success",
                "total_artifacts": len(updated_registry),
                "registry_path": str(registry_path),
                "timestamp": "verification_complete"
            }, f, indent=2)
        logger.info(f"Verification report written to {report_path}")
        return 0
    else:
        logger.error("Verification failed. Some artifacts have mismatched hashes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())