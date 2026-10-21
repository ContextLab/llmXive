"""
State-management helper for artifact hash tracking (T006).

Records SHA-256 checksums and metadata for project artifacts in a
project-owned manifest under ``data/state/``. Per platform rules the
canonical ``state/`` directory is owned by the platform, so this helper
deliberately writes only inside ``data/`` (a project-owned path).
"""

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "data" / "state"
MANIFEST_PATH = STATE_DIR / "manifest.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_state_dir() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def _relpath(file_path: Union[str, Path]) -> str:
    path = Path(file_path).resolve()
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _load_manifest() -> Dict[str, Any]:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"artifacts": {}, "last_updated": None}


def _save_manifest(manifest: Dict[str, Any]) -> None:
    _ensure_state_dir()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def get_artifact_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Compute checksum and metadata for an artifact file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")
    stat = path.stat()
    return {
        "path": _relpath(path),
        "checksum": _sha256(path),
        "size_bytes": stat.st_size,
        "modified_at": datetime.datetime.fromtimestamp(
            stat.st_mtime
        ).isoformat(),
    }


def update_state_for_artifact(
    file_path: Union[str, Path],
    task_id: str,
    description: str = "",
    dependencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Record (or refresh) the hash entry for an artifact in the
    project-owned state manifest at ``data/state/manifest.json``.

    Returns the manifest entry written.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Cannot update state for non-existent file: {file_path}"
        )

    metadata = get_artifact_metadata(path)
    entry = {
        "task_id": task_id,
        "description": description,
        "dependencies": dependencies or [],
        "metadata": metadata,
        "updated_at": datetime.datetime.now().isoformat(),
    }

    manifest = _load_manifest()
    manifest.setdefault("artifacts", {})[metadata["path"]] = entry
    manifest["last_updated"] = entry["updated_at"]
    _save_manifest(manifest)
    return entry


def get_artifact_state(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Return the recorded manifest entry for an artifact, or None."""
    manifest = _load_manifest()
    return manifest.get("artifacts", {}).get(_relpath(file_path))


def verify_artifact_integrity(file_path: Union[str, Path]) -> bool:
    """True iff the file's current checksum matches the recorded one."""
    entry = get_artifact_state(file_path)
    if entry is None:
        return False
    return _sha256(Path(file_path)) == entry["metadata"]["checksum"]


def list_artifacts() -> Dict[str, Dict[str, Any]]:
    """Return all registered artifact entries."""
    return _load_manifest().get("artifacts", {})


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Track artifact hashes in data/state/manifest.json."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_update = sub.add_parser("update", help="Record an artifact's hash")
    p_update.add_argument("file_path")
    p_update.add_argument("--task", required=True)
    p_update.add_argument("--desc", default="")
    p_update.add_argument("--deps", nargs="*", default=[])

    p_verify = sub.add_parser("verify", help="Verify an artifact's hash")
    p_verify.add_argument("file_path")

    sub.add_parser("list", help="List registered artifacts")

    args = parser.parse_args(argv)

    if args.command == "update":
        try:
            entry = update_state_for_artifact(
                args.file_path, args.task, args.desc, args.deps
            )
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        print(f"Recorded: {entry['metadata']['path']}")
        print(f"Checksum: {entry['metadata']['checksum']}")
        return 0

    if args.command == "verify":
        ok = verify_artifact_integrity(args.file_path)
        print("Integrity verified" if ok else "Integrity check FAILED")
        return 0 if ok else 1

    if args.command == "list":
        artifacts = list_artifacts()
        if not artifacts:
            print("No artifacts registered.")
        for rel, entry in artifacts.items():
            print(f"{rel}\t{entry['metadata']['checksum']}\t{entry['task_id']}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
