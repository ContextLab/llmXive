"""
Artifact hashing utility for Constitution Principle V (Fail Fast).

This script computes SHA-256 hashes for all critical project artifacts
to ensure data integrity and reproducibility. It validates that the
project state matches the recorded hashes, preventing silent corruption
or unauthorized modifications.

Usage:
    python scripts/hash_artifacts.py [--check] [--output data/hashes.json]

Options:
    --check    Compare current hashes against data/hashes.json
    --output   Path to write the new hash manifest (default: data/hashes.json)
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Project root is assumed to be the parent of 'scripts'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"

# Patterns of files to hash (critical artifacts)
CRITICAL_PATTERNS = [
    "data/processed/*.csv",
    "data/processed/*.json",
    "data/raw/*.json",
    "data/raw/*.log",
    "contracts/*.schema.yaml",
    "docs/protocol.md",
    "docs/results.md",
    "docs/analysis-plan.md",
    "docs/ethics_determination.md",
    "code/**/*.py",
    "tests/**/*.py",
]

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to hash {file_path}: {e}")

def find_critical_files(base_dir: Path, patterns: List[str]) -> List[Path]:
    """Find files matching the critical patterns."""
    found_files = []
    for pattern in patterns:
        # Convert glob pattern to relative path from base_dir
        # Handle ** for recursive search
        if "**" in pattern:
            # Use rglob for recursive search
            parts = pattern.split("/")
            # Find the first part that contains **
            for i, part in enumerate(parts):
                if "**" in part:
                    prefix = "/".join(parts[:i])
                    suffix = "/".join(parts[i+1:])
                    if prefix:
                        search_dir = base_dir / prefix
                    else:
                        search_dir = base_dir
                    for file in search_dir.rglob(suffix):
                        if file.is_file():
                            found_files.append(file)
                    break
        else:
            # Simple glob
            for file in base_dir.glob(pattern):
                if file.is_file():
                    found_files.append(file)
    return sorted(found_files)

def generate_manifest(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Generate a manifest of hashes for all critical artifacts."""
    if output_path is None:
        output_path = DATA_DIR / "hashes.json"

    all_files = []
    for pattern in CRITICAL_PATTERNS:
        # Determine base directory for pattern
        if pattern.startswith("data/"):
            base = DATA_DIR
        elif pattern.startswith("contracts/"):
            base = CONTRACTS_DIR
        elif pattern.startswith("docs/"):
            base = DOCS_DIR
        elif pattern.startswith("code/"):
            base = CODE_DIR
        elif pattern.startswith("tests/"):
            base = TESTS_DIR
        else:
            base = PROJECT_ROOT

        files = find_critical_files(base, [pattern])
        # Adjust paths to be relative to PROJECT_ROOT
        for f in files:
            rel_path = f.relative_to(PROJECT_ROOT)
            all_files.append((str(rel_path), f))

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "artifacts": []
    }

    for rel_path, abs_path in all_files:
        try:
            file_hash = compute_file_hash(abs_path)
            file_size = abs_path.stat().st_size
            manifest["artifacts"].append({
                "path": rel_path,
                "sha256": file_hash,
                "size_bytes": file_size
            })
        except Exception as e:
            print(f"Warning: Skipping {rel_path} due to error: {e}", file=sys.stderr)

    # Write manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest generated: {output_path}")
    print(f"Total artifacts hashed: {len(manifest['artifacts'])}")
    return manifest

def verify_manifest(manifest_path: Optional[Path] = None) -> bool:
    """Verify current artifacts against a stored manifest."""
    if manifest_path is None:
        manifest_path = DATA_DIR / "hashes.json"

    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}", file=sys.stderr)
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Verifying against manifest: {manifest_path}")
    print(f"Generated at: {manifest.get('generated_at', 'unknown')}")
    print("-" * 60)

    all_valid = True
    errors = []

    for artifact in manifest["artifacts"]:
        rel_path = artifact["path"]
        expected_hash = artifact["sha256"]
        abs_path = PROJECT_ROOT / rel_path

        if not abs_path.exists():
            errors.append(f"MISSING: {rel_path}")
            all_valid = False
            print(f"❌ MISSING: {rel_path}")
            continue

        try:
            current_hash = compute_file_hash(abs_path)
            if current_hash == expected_hash:
                print(f"✅ OK: {rel_path}")
            else:
                errors.append(f"MISMATCH: {rel_path} (expected {expected_hash[:16]}..., got {current_hash[:16]}...)")
                all_valid = False
                print(f"❌ MISMATCH: {rel_path}")
        except Exception as e:
            errors.append(f"ERROR: {rel_path} - {e}")
            all_valid = False
            print(f"❌ ERROR: {rel_path} - {e}")

    print("-" * 60)
    if all_valid:
        print("✅ All artifacts verified successfully.")
        return True
    else:
        print(f"❌ Verification failed. {len(errors)} error(s) found.")
        for err in errors:
            print(f"   {err}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Hash critical project artifacts for integrity verification."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify current artifacts against stored manifest"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write the hash manifest (default: data/hashes.json)"
    )

    args = parser.parse_args()

    if args.check:
        success = verify_manifest()
        sys.exit(0 if success else 1)
    else:
        output_path = Path(args.output) if args.output else None
        try:
            generate_manifest(output_path)
            sys.exit(0)
        except Exception as e:
            print(f"Error generating manifest: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()