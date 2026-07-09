"""
Artifact Hashing Utility for Constitution Principle V.

This script computes and records cryptographic hashes for all research artifacts
to ensure data integrity and reproducibility. It supports:
- SHA-256 hashing of all files in specified directories
- JSON output manifest for audit trails
- Verification of existing manifests against current file states
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_config, get_data_path, get_code_path
from utils.logging import get_logger, log_event

# Configure logger
logger = get_logger("hash_artifacts")

# Directories to hash
HASH_TARGETS = [
    ("code", get_code_path()),
    ("data/raw", get_data_path("raw")),
    ("data/processed", get_data_path("processed")),
    ("contracts", PROJECT_ROOT / "contracts"),
    ("specs", PROJECT_ROOT / "specs"),
]

# Output manifest path
MANIFEST_PATH = PROJECT_ROOT / "data" / "artifacts" / "hash_manifest.json"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash {file_path}: {e}")
        raise


def hash_directory(base_path: Path, relative_prefix: str) -> List[Dict[str, str]]:
    """Recursively hash all files in a directory."""
    results = []
    if not base_path.exists():
        logger.warning(f"Directory does not exist: {base_path}")
        return results

    for file_path in base_path.rglob("*"):
        if file_path.is_file() and not file_path.name.endswith(".json"):
            # Skip the manifest itself
            try:
                rel_path = file_path.relative_to(PROJECT_ROOT)
                hash_value = compute_sha256(file_path)
                results.append({
                    "path": str(rel_path),
                    "hash": hash_value,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime, tz=timezone.utc
                    ).isoformat()
                })
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

    return results


def generate_manifest() -> Dict:
    """Generate a complete hash manifest for all artifacts."""
    logger.info("Starting artifact hashing process...")
    start_time = datetime.now(timezone.utc)

    manifest = {
        "generated_at": start_time.isoformat(),
        "project": "PROJ-008-psychology-research",
        "version": "1.0.0",
        "artifacts": []
    }

    for target_name, target_path in HASH_TARGETS:
        if not target_path.exists():
            logger.info(f"Skipping non-existent target: {target_name}")
            continue

        logger.info(f"Hashing {target_name}...")
        artifacts = hash_directory(target_path, target_name)
        manifest["artifacts"].extend(artifacts)

    manifest["total_artifacts"] = len(manifest["artifacts"])
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Ensure output directory exists
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {MANIFEST_PATH}")
    log_event("artifact_hashing_complete", {
        "total_artifacts": manifest["total_artifacts"],
        "manifest_path": str(MANIFEST_PATH)
    })

    return manifest


def verify_manifest(manifest_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Verify current file hashes against a stored manifest."""
    manifest_path = manifest_path or MANIFEST_PATH

    if not manifest_path.exists():
        return False, [f"Manifest not found: {manifest_path}"]

    with open(manifest_path, "r", encoding="utf-8") as f:
        stored_manifest = json.load(f)

    mismatches = []
    current_artifacts = {}

    # Re-hash all artifacts
    for target_name, target_path in HASH_TARGETS:
        if not target_path.exists():
            continue
        artifacts = hash_directory(target_path, target_name)
        for artifact in artifacts:
            current_artifacts[artifact["path"]] = artifact["hash"]

    # Compare with stored manifest
    for entry in stored_manifest.get("artifacts", []):
        path = entry["path"]
        stored_hash = entry["hash"]

        if path not in current_artifacts:
            mismatches.append(f"MISSING: {path}")
        elif current_artifacts[path] != stored_hash:
            mismatches.append(f"MODIFIED: {path} (hash mismatch)")

    # Check for new files not in manifest
    for path in current_artifacts:
        if not any(a["path"] == path for a in stored_manifest.get("artifacts", [])):
            mismatches.append(f"NEW: {path}")

    is_valid = len(mismatches) == 0
    return is_valid, mismatches


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Artifact hashing utility for Constitution Principle V")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify current artifacts against stored manifest"
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate a new hash manifest"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=str(MANIFEST_PATH),
        help="Path to manifest file for verification"
    )

    args = parser.parse_args()

    if args.verify:
        is_valid, mismatches = verify_manifest(Path(args.manifest))
        if is_valid:
            logger.info("✓ All artifacts verified successfully")
            sys.exit(0)
        else:
            logger.error("✗ Artifact verification failed:")
            for mismatch in mismatches:
                logger.error(f"  - {mismatch}")
            sys.exit(1)

    elif args.generate:
        generate_manifest()
        logger.info("✓ Manifest generation complete")
        sys.exit(0)

    else:
        # Default action: generate new manifest
        logger.info("No action specified. Generating new manifest...")
        generate_manifest()


if __name__ == "__main__":
    main()
