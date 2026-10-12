"""
Optical Flow Loader

This script copies (or symlinks) pre‑computed FlowNet‑C optical‑flow feature
files (stored as ``.npy``) from a repository bundle into the project's
``data/flow_features/`` directory.  If a checksum manifest is present, each
copied file is verified against its SHA‑256 hash.

The loader is deliberately CPU‑only – no flow computation is performed.
It is used by downstream tasks (e.g. model training) that expect the
features to be available under ``data/flow_features/``.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path
from typing import Dict

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

MANIFEST_REL_PATH = Path("checksums") / "flow_features_manifest.csv"


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
        log.debug("Checksum manifest %s not found – skipping verification.", manifest_path)
        return {}

    checksums: Dict[Path, str] = {}
    with manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rel_path_str, sha256 = line.split(",", 1)
            except ValueError:
                raise ValueError(f"Malformed manifest line: {line!r}")
            checksums[Path(rel_path_str)] = sha256.strip()
    return checksums


def copy_or_symlink(
    src_dir: Path,
    dst_dir: Path,
    use_symlink: bool = False,
    manifest: Dict[Path, str] | None = None,
) -> None:
    """
    Copy (or symlink) all ``.npy`` files from ``src_dir`` into ``dst_dir``.

    Parameters
    ----------
    src_dir: Path
        Directory containing the bundled FlowNet‑C ``.npy`` files.
    dst_dir: Path
        Destination directory – created if it does not exist.
    use_symlink: bool, default False
        If True, create symbolic links instead of copying the files.
    manifest: dict | None
        Mapping of relative file paths (relative to the repository root)
        to expected SHA‑256 checksums.  If provided, each copied file is
        verified against the stored checksum; a mismatch raises ``ValueError``.
    """
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Source directory {src_dir!s} does not exist or is not a directory.")

    dst_dir.mkdir(parents=True, exist_ok=True)
    log.info("Preparing destination directory %s", dst_dir)

    for src_file in src_dir.rglob("*.npy"):
        if not src_file.is_file():
            continue

        rel_path = src_file.relative_to(src_dir.parent)  # relative to repo root
        dst_file = dst_dir / src_file.name

        if use_symlink:
            if dst_file.exists():
                dst_file.unlink()
            os.symlink(src_file.resolve(), dst_file)
            action = "symlinked"
        else:
            shutil.copy2(src_file, dst_file)
            action = "copied"

        log.debug("%s %s → %s", action.capitalize(), src_file, dst_file)

        # Verify checksum if we have a manifest entry for this file
        if manifest is not None and rel_path in manifest:
            expected = manifest[rel_path]
            actual = _sha256_of_file(dst_file)
            if actual != expected:
                raise ValueError(
                    f"Checksum mismatch for {dst_file!s}: expected {expected}, got {actual}"
                )
            else:
                log.debug("Checksum verified for %s", dst_file)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load pre‑computed optical‑flow features (CPU‑only)."
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to the directory containing the bundled FlowNet‑C ``.npy`` files.",
    )
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="Create symbolic links instead of copying files. Useful for large bundles.",
    )
    args = parser.parse_args()

    # Destination directory inside the project (creates the folder if needed)
    dest_dir = paths.data("flow_features")

    # Load checksum manifest if it exists; the manifest is expected to live at
    # ``data/checksums/flow_features_manifest.csv``.  The manifest will be
    # generated later by task T014; until then verification is skipped.
    manifest_path = paths.data(MANIFEST_REL_PATH)
    manifest = _load_manifest(manifest_path)

    copy_or_symlink(
        src_dir=args.source,
        dst_dir=dest_dir,
        use_symlink=args.symlink,
        manifest=manifest or None,
    )
    log.info("Optical‑flow feature loading complete. %d files now reside in %s", len(list(dest_dir.glob("*.npy"))), dest_dir)


if __name__ == "__main__":
    main()