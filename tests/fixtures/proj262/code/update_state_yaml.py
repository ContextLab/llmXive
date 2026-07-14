"""Update the project state YAML with timestamps and SHA256 hashes.

This script scans the repository (excluding the generated state file itself)
and writes a YAML file at ``state/projects/001-predicting-molecular-dipole-moments.yaml``
containing, for each file, the UTC timestamp of the scan and the file's SHA256 hash.

The output format is:

.. code-block:: yaml

    files:
      - path: relative/path/to/file.py
        timestamp: 2026-06-24T12:34:56Z
        sha256: abcdef...

The script can be executed directly::

    python -m code.update_state_yaml

or imported and called via :func:`main`.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

def _iter_repository_files(root: Path) -> list[Path]:
    """Yield all files under *root* that should be tracked.

    The state file itself is excluded to avoid a circular reference.
    Hidden directories (e.g., ``.git``) are also ignored.
    """
    exclude = {
        root / "state" / "projects" / "001-predicting-molecular-dipole-moments.yaml",
    }
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            # skip hidden directories/files like .git, .venv, etc.
            continue
        if path in exclude:
            continue
        yield path

def _hash_file(path: Path) -> str:
    """Return the SHA256 hex digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def generate_state_yaml(root: Path) -> str:
    """Generate the YAML content for the repository state."""
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = ["files:"]
    for file_path in sorted(_iter_repository_files(root)):
        rel_path = file_path.relative_to(root).as_posix()
        file_hash = _hash_file(file_path)
        lines.append(f"- path: {rel_path}")
        lines.append(f"  timestamp: {timestamp}")
        lines.append(f"  sha256: {file_hash}")
    return "\n".join(lines) + "\n"

def main(argv: list[str] | None = None) -> int:
    """Entry point for the script.

    Writes the generated YAML to the required location and returns an exit code.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Resolve the repository root (the directory containing this file's grand‑parent)
    repo_root = Path(__file__).resolve().parents[2]  # code/../ -> project root
    output_path = repo_root / "state" / "projects" / "001-predicting-molecular-dipole-moments.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = generate_state_yaml(repo_root)
    output_path.write_text(yaml_content, encoding="utf-8")
    print(f"State file written to {output_path}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
