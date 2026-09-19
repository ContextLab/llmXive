#!/usr/bin/env python
"""
Calculate SHA256 hashes for artifacts and update state.
"""
import argparse
import json
import hashlib
import sys
from pathlib import Path
import logging

from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def version_artifact(config, artifact_path: Path):
    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        sys.exit(1)

    file_hash = calculate_sha256(artifact_path)
    logger.info(f"Artifact {artifact_path} hashed: {file_hash}")

    # Update state
    state_dir = Path(config.get_path("PROJECT_ROOT")) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "artifact_versions.json"

    state = {}
    if state_file.exists():
        with open(state_file, "r") as f:
            state = json.load(f)

    state[str(artifact_path)] = file_hash

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    logger.info(f"State updated in {state_file}")

def main():
    parser = argparse.ArgumentParser(description="Version artifacts")
    parser.add_argument("--artifact", type=str, required=True, help="Path to artifact")
    args = parser.parse_args()

    config = get_config()
    artifact_path = Path(args.artifact)
    version_artifact(config, artifact_path)

if __name__ == "__main__":
    main()
