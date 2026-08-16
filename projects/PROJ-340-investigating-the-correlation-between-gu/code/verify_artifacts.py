"""
Artifact Verification Script for llmXive Pipeline.

This script recalculates checksums for all generated artifacts and compares them
against the recorded hashes in the project state file. It ensures data integrity
and reproducibility (Constitution Principle III).

Usage:
    python code/verify_artifacts.py [--state STATE_FILE] [--verbose]
"""

import os
import sys
import json
import hashlib
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-340-investigating-the-correlation-between-gu.yaml"
ARTIFACT_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "data" / "results",
    PROJECT_ROOT / "data" / "metadata",
    PROJECT_ROOT / "data" / "config",
    PROJECT_ROOT / "data" / "citations",
]
EXCLUDED_FILES = {".gitkeep", ".DS_Store", "Thumbs.db"}


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")


def load_state_file(state_file: Path) -> Dict:
    """
    Load the project state file containing artifact hashes.

    Args:
        state_file: Path to the state YAML file.

    Returns:
        Dictionary containing the state data.

    Raises:
        FileNotFoundError: If the state file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")

    with open(state_file, "r") as f:
        return yaml.safe_load(f)


def discover_artifacts(base_dirs: List[Path]) -> List[Path]:
    """
    Discover all relevant artifact files in the specified directories.

    Args:
        base_dirs: List of base directories to search.

    Returns:
        List of Path objects for discovered artifact files.
    """
    artifacts = []
    for base_dir in base_dirs:
        if not base_dir.exists():
            continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file in EXCLUDED_FILES:
                    continue
                file_path = Path(root) / file
                # Only include specific file types
                if file_path.suffix in {".csv", ".parquet", ".json", ".yaml", ".yml", ".md", ".txt", ".png", ".pdf"}:
                    artifacts.append(file_path)
    return artifacts


def verify_artifacts(state_file: Path, artifacts: Optional[List[Path]] = None, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Verify artifacts against recorded checksums in the state file.

    Args:
        state_file: Path to the state YAML file.
        artifacts: Optional list of artifacts to verify. If None, discovers them.
        verbose: If True, prints detailed output.

    Returns:
        Tuple of (all_verified: bool, messages: List[str])
    """
    messages = []
    all_verified = True

    try:
        state_data = load_state_file(state_file)
    except (FileNotFoundError, yaml.YAMLError) as e:
        msg = f"Error loading state file: {e}"
        messages.append(msg)
        return False, messages

    artifact_hashes = state_data.get("artifact_hashes", {})
    if not artifact_hashes:
        msg = "No artifact hashes found in state file. Nothing to verify."
        messages.append(msg)
        if verbose:
            print(msg)
        return True, messages

    if artifacts is None:
        artifacts = discover_artifacts(ARTIFACT_DIRS)

    if not artifacts:
        msg = "No artifacts found in the specified directories."
        messages.append(msg)
        if verbose:
            print(msg)
        # Not necessarily a failure if no artifacts are expected yet
        return True, messages

    verified_count = 0
    missing_count = 0
    mismatch_count = 0

    for artifact_path in artifacts:
        relative_path = str(artifact_path.relative_to(PROJECT_ROOT))
        recorded_hash = artifact_hashes.get(relative_path)

        if not recorded_hash:
            msg = f"⚠ No recorded hash for: {relative_path}"
            messages.append(msg)
            if verbose:
                print(msg)
            # Missing hash is not a verification failure, just a warning
            continue

        try:
            current_hash = calculate_file_checksum(artifact_path)
            if current_hash == recorded_hash:
                verified_count += 1
                if verbose:
                    print(f"✓ Verified: {relative_path}")
            else:
                mismatch_count += 1
                all_verified = False
                msg = f"✗ MISMATCH: {relative_path}"
                messages.append(msg)
                if verbose:
                    print(f"  Expected: {recorded_hash}")
                    print(f"  Found:    {current_hash}")
        except (FileNotFoundError, PermissionError) as e:
            missing_count += 1
            all_verified = False
            msg = f"✗ MISSING/ERROR: {relative_path} - {e}"
            messages.append(msg)
            if verbose:
                print(msg)

    summary = f"\nVerification Summary: {verified_count} verified, {missing_count} missing, {mismatch_count} mismatched."
    messages.append(summary)
    if verbose:
        print(summary)

    if all_verified:
        messages.append("✅ All verified artifacts match their recorded checksums.")
    else:
        messages.append("❌ Verification failed: Some artifacts are missing or mismatched.")

    return all_verified, messages


def main():
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(
        description="Verify artifact checksums against the project state file."
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE_FILE,
        help=f"Path to the state YAML file (default: {DEFAULT_STATE_FILE})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed verification output.",
    )
    parser.add_argument(
        "--artifacts",
        nargs="+",
        type=Path,
        default=None,
        help="Specific artifacts to verify (relative to project root).",
    )

    args = parser.parse_args()

    # Resolve state file path
    state_file = args.state
    if not state_file.is_absolute():
        state_file = PROJECT_ROOT / state_file

    # Convert relative artifact paths to absolute
    artifacts = None
    if args.artifacts:
        artifacts = [
            p if p.is_absolute() else PROJECT_ROOT / p for p in args.artifacts
        ]

    print(f"Verifying artifacts against state file: {state_file}")
    print("-" * 50)

    try:
        all_verified, messages = verify_artifacts(state_file, artifacts, args.verbose)

        for msg in messages:
            print(msg)

        sys.exit(0 if all_verified else 1)

    except Exception as e:
        print(f"❌ Unexpected error during verification: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()