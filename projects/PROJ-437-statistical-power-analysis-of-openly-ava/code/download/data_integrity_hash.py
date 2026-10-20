"""
Data Integrity Hash
-------------------
Walks a directory tree, computes SHA‑256 hashes for every file, and
writes a JSON manifest to ``data/derived/integrity_hashes.json``.
Downstream modules can import ``load_integrity_manifest`` to obtain the
mapping ``{relative_path: sha256}``.
"""

import json
from pathlib import Path
from typing import Dict

from .corruption_handler import compute_sha256

def generate_integrity_manifest(root_dir: Path) -> Dict[str, str]:
    """
    Compute SHA‑256 hashes for all regular files under ``root_dir``.
    Returns a dictionary mapping *relative* POSIX paths to their hash.
    """
    manifest: Dict[str, str] = {}
    for file_path in root_dir.rglob("*"):
        if file_path.is_file():
            rel = file_path.relative_to(root_dir).as_posix()
            manifest[rel] = compute_sha256(file_path)
    return manifest


def write_integrity_manifest(root_dir: Path, output_path: Path) -> None:
    """
    Compute the manifest and write it as pretty‑printed JSON.
    """
    manifest = generate_integrity_manifest(root_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def load_integrity_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load a previously written integrity manifest.
    """
    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)
