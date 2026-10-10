"""
Hash Management Module for Artifact Integrity Verification.

Implements T017c: Robust Hash Initialization

Computes SHA-256 of solvents.yaml and stores under state/artifact_hashes.yaml.
Raises if file missing.
"""

import os
import sys
import json
import logging
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Import from existing API surface
from config import get_chemicals_path

logger = logging.getLogger(__name__)

class HashVerificationError(Exception):
    """Raised when hash verification fails or file is missing."""
    pass


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal SHA-256 hash string.
        
    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def load_artifact_hashes(hashes_file: Path) -> Dict[str, Any]:
    """
    Load existing artifact hashes from file.
    
    Args:
        hashes_file: Path to the artifact_hashes.yaml file.
        
    Returns:
        Dictionary of artifact hashes, or empty dict if file does not exist.
    """
    if not hashes_file.exists():
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hashes": {}
        }
    
    try:
        with open(hashes_file, 'r', encoding='utf-8') as f:
            import yaml
            data = yaml.safe_load(f)
            return data if data else {"timestamp": datetime.now(timezone.utc).isoformat(), "hashes": {}}
    except ImportError:
        # Fallback to JSON if yaml is not available
        with open(hashes_file, 'r', encoding='utf-8') as f:
            return json.load(f)


def save_artifact_hashes(hashes_data: Dict[str, Any], hashes_file: Path) -> None:
    """
    Save artifact hashes to file.
    
    Args:
        hashes_data: Dictionary containing hashes.
        hashes_file: Path to the artifact_hashes.yaml file.
    """
    # Ensure directory exists
    hashes_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        import yaml
        with open(hashes_file, 'w', encoding='utf-8') as f:
            yaml.dump(hashes_data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON if yaml is not available
        with open(hashes_file, 'w', encoding='utf-8') as f:
            json.dump(hashes_data, f, indent=2)


def initialize_solvents_hash(solvents_file: Optional[Path] = None, 
                             hashes_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Compute SHA-256 of solvents.yaml and store in artifact_hashes.yaml.
    
    This is the core function for T017c: Robust Hash Initialization.
    
    Args:
        solvents_file: Path to solvents.yaml. If None, uses default from config.
        hashes_file: Path to artifact_hashes.yaml. If None, uses state/artifact_hashes.yaml.
        
    Returns:
        Dictionary containing the hash record.
        
    Raises:
        HashVerificationError: If solvents.yaml is missing.
    """
    # Determine file paths
    if solvents_file is None:
        chemicals_path = get_chemicals_path()
        solvents_file = chemicals_path / "solvents.yaml"
    
    if hashes_file is None:
        state_dir = Path("state")
        hashes_file = state_dir / "artifact_hashes.yaml"
    
    # Verify solvents.yaml exists
    if not solvents_file.exists():
        error_msg = (
            f"solvents.yaml not found at {solvents_file}. "
            "Cannot initialize hash. Ensure T006b (Solvent Data Population) "
            "has completed and solvents.yaml exists in the chemicals directory."
        )
        logger.error(error_msg)
        raise HashVerificationError(error_msg)
    
    # Compute hash
    logger.info(f"Computing SHA-256 hash of {solvents_file}")
    solvents_hash = compute_sha256(solvents_file)
    logger.info(f"Computed hash: {solvents_hash}")
    
    # Load existing hashes
    hashes_data = load_artifact_hashes(hashes_file)
    
    # Update with new hash
    if "hashes" not in hashes_data:
        hashes_data["hashes"] = {}
    
    hashes_data["hashes"]["solvents_yaml_hash"] = solvents_hash
    hashes_data["timestamp"] = datetime.now(timezone.utc).isoformat()
    hashes_data["solvents_yaml_path"] = str(solvents_file)
    
    # Save updated hashes
    logger.info(f"Saving artifact hashes to {hashes_file}")
    save_artifact_hashes(hashes_data, hashes_file)
    
    logger.info("Hash initialization complete")
    
    return {
        "artifact": "solvents.yaml",
        "hash": solvents_hash,
        "path": str(solvents_file),
        "timestamp": hashes_data["timestamp"],
        "stored_in": str(hashes_file)
    }


def verify_solvents_hash(solvents_file: Optional[Path] = None,
                        hashes_file: Optional[Path] = None) -> bool:
    """
    Verify that solvents.yaml hash matches the stored hash.
    
    Args:
        solvents_file: Path to solvents.yaml.
        hashes_file: Path to artifact_hashes.yaml.
        
    Returns:
        True if hash matches, False otherwise.
        
    Raises:
        HashVerificationError: If files are missing or hash not found.
    """
    # Determine file paths
    if solvents_file is None:
        chemicals_path = get_chemicals_path()
        solvents_file = chemicals_path / "solvents.yaml"
    
    if hashes_file is None:
        state_dir = Path("state")
        hashes_file = state_dir / "artifact_hashes.yaml"
    
    # Verify files exist
    if not solvents_file.exists():
        raise HashVerificationError(f"solvents.yaml not found at {solvents_file}")
    
    if not hashes_file.exists():
        raise HashVerificationError(f"artifact_hashes.yaml not found at {hashes_file}")
    
    # Load stored hash
    hashes_data = load_artifact_hashes(hashes_file)
    stored_hash = hashes_data.get("hashes", {}).get("solvents_yaml_hash")
    
    if not stored_hash:
        raise HashVerificationError(
            "solvents_yaml_hash not found in artifact_hashes.yaml. "
            "Run hash initialization first."
        )
    
    # Compute current hash
    current_hash = compute_sha256(solvents_file)
    
    # Compare
    if current_hash == stored_hash:
        logger.info("Hash verification passed: solvents.yaml is unchanged")
        return True
    else:
        logger.warning(
            f"Hash mismatch for solvents.yaml. "
            f"Stored: {stored_hash}, Current: {current_hash}"
        )
        return False


def main():
    """CLI entry point for hash initialization and verification."""
    parser = argparse.ArgumentParser(
        description="Initialize and verify artifact hashes for reproducibility."
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["init", "verify"],
        default="init",
        help="Action to perform: 'init' to initialize hashes, 'verify' to check them."
    )
    parser.add_argument(
        "--solvents-file",
        type=str,
        default=None,
        help="Path to solvents.yaml (optional; uses default if not provided)."
    )
    parser.add_argument(
        "--hashes-file",
        type=str,
        default=None,
        help="Path to artifact_hashes.yaml (optional; uses default if not provided)."
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        solvents_path = Path(args.solvents_file) if args.solvents_file else None
        hashes_path = Path(args.hashes_file) if args.hashes_file else None
        
        if args.action == "init":
            result = initialize_solvents_hash(solvents_path, hashes_path)
            print(json.dumps(result, indent=2))
            return 0
        
        elif args.action == "verify":
            is_valid = verify_solvents_hash(solvents_path, hashes_path)
            if is_valid:
                print("Hash verification passed")
                return 0
            else:
                print("Hash verification failed: solvents.yaml has been modified")
                return 1
    
    except HashVerificationError as e:
        logger.error(f"Hash verification error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
