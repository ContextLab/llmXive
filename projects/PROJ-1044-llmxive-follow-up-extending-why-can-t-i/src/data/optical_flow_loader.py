"""
Utility to copy or symlink pre‑computed optical‑flow ``.npy`` files into a
target directory. This is useful for test setups that expect the
``flow_features`` directory to contain files but do not need actual flow
data (the counterfactual generator falls back to on‑the‑fly computation).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _sha256_of_file(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_manifest(manifest_path: Path) -> Dict[Path, str]:
    """
    Load a CSV manifest of ``relative_path,sha256`` into a dict.

    The manifest is expected to use POSIX‑style relative paths (as
    produced by ``data/checksums/manifest.csv``).  If the manifest does not
    exist, an empty dict is returned.
    """
    if not manifest_path.is_file():
        return {}
    mapping: Dict[Path, str] = {}
    with manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rel, sha = line.split(",", 1)
            mapping[Path(rel)] = sha
    return mapping

def copy_or_symlink(
    src_dir: Path,
    dst_dir: Path,
    use_symlink: bool = False,
    manifest: Dict[Path, str] | None = None,
) -> int:
    """
    Copy (or symlink) all ``.npy`` files from ``src_dir`` into ``dst_dir``.

    Parameters
    ----------
    src_dir: Path
        Directory containing the bundled FlowNet‑C ``.npy`` files.
    dst_dir: Path
        Destination directory - created if it does not exist.
    use_symlink: bool, default False
        If True, create symbolic links instead of copying the files.
    manifest: dict | None
        Mapping of relative file paths (relative to the repository root)
        to expected SHA‑256 checksums.  If provided, each copied file is
        verified against the stored checksum; a mismatch raises ``ValueError``.

    Returns
    -------
    int
        Number of ``.npy`` files materialised in ``dst_dir``.
    """
    src_dir.mkdir(parents=True, exist_ok=True)
    dst_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for npy_path in src_dir.rglob("*.npy"):
        rel_path = npy_path.relative_to(src_dir)
        dst_path = dst_dir / rel_path

        if manifest is not None:
            expected = manifest.get(rel_path)
            actual = _sha256_of_file(npy_path)
            if expected != actual:
                raise ValueError(
                    f"Checksum mismatch for {npy_path}: expected {expected}, got {actual}"
                )

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if use_symlink:
            if dst_path.is_symlink() or dst_path.exists():
                dst_path.unlink()
            os.symlink(npy_path, dst_path)
        else:
            shutil.copy2(npy_path, dst_path)
        count += 1

    log.info("Materialised %d .npy files from %s to %s", count, src_dir, dst_dir)
    return count

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy or symlink optical‑flow .npy files."
    )
    parser.add_argument(
        "src_dir",
        type=Path,
        help="Source directory containing .npy files.",
    )
    parser.add_argument(
        "dst_dir",
        type=Path,
        help="Destination directory.",
    )
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="Create symbolic links instead of copying files.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional manifest CSV for checksum verification.",
    )
    args = parser.parse_args(argv)

    manifest = _load_manifest(args.manifest) if args.manifest else None
    return copy_or_symlink(args.src_dir, args.dst_dir, args.symlink, manifest)