"""T016 / FR-008: Compute SHA-256 hashes for generated artifacts and
update the project state YAML (Constitution Principle V).

Hashes the twin-prime CSV produced by US1 (data/raw/twin_primes.csv)
plus all JSON results and figures, updates the project state YAML,
and writes a durable copy of the hash manifest to
results/artifact_hashes.json (outside gitignored dataset caches).

The execution guard for code/generate_primes.py
(check_execution_guard, exiting with code 1 when neither primesieve
nor numpy is usable) is already part of that module and is invoked
from its main(); this module completes T016 by hashing its output.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

try:
    from llmxive_toolkit import paths
except ImportError:  # pragma: no cover - toolkit is always present
    paths = None

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import get_config, get_state_path
except ImportError:  # pragma: no cover
    get_config = None
    get_state_path = None


def _project_root() -> Path:
    if paths is not None:
        return Path(paths.root)
    return Path(__file__).resolve().parent.parent


def compute_sha256(file_path) -> str:
    """Compute SHA-256 hash of a file."""
    file_path = Path(file_path)
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _collect_dir(directory: Path, extensions) -> List[Path]:
    found: List[Path] = []
    if not directory.exists():
        return found
    for root, _, files in os.walk(directory):
        for file in sorted(files):
            if file.endswith(tuple(extensions)):
                found.append(Path(root) / file)
    return sorted(found)


def get_artifacts_to_hash(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Return a list of artifact file paths that should be hashed.

    Includes the raw twin-prime CSV, all JSON/CSV results, all
    figures, and durable copies under results/.
    """
    root = _project_root()
    artifacts: List[Path] = []

    csv = root / "data" / "raw" / "twin_primes.csv"
    if csv.exists():
        artifacts.append(csv)

    artifacts.extend(_collect_dir(root / "data" / "results", (".json", ".csv")))
    artifacts.extend(_collect_dir(root / "data" / "figures", (".png", ".pdf")))
    artifacts.extend(_collect_dir(root / "results", (".json", ".csv")))

    # Deduplicate while preserving order
    seen = set()
    unique: List[Path] = []
    for a in artifacts:
        rp = a.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(a)
    return [str(a) for a in unique]


def update_state_file(state_path, hashes: Dict[str, str], metadata: Dict[str, Any]) -> None:
    """Update the project state YAML file with new hashes and metadata.

    Creates the file (and its parent directory) if it doesn't exist.
    """
    state_path = Path(state_path)
    state: Dict[str, Any] = {"artifacts": {}}
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                state = yaml.safe_load(f) or {"artifacts": {}}
        except yaml.YAMLError:
            state = {"artifacts": {}}
    if not isinstance(state, dict):
        state = {"artifacts": {}}
    state.setdefault("artifacts", {})
    root = _project_root()
    for path, hash_val in hashes.items():
        try:
            key = str(Path(path).resolve().relative_to(root))
        except ValueError:
            key = str(path)
        state["artifacts"][key] = {"hash": hash_val}
    state.setdefault("metadata", {}).update(metadata)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def _resolve_state_path() -> Path:
    root = _project_root()
    if get_state_path is not None:
        try:
            sp = Path(get_state_path())
            if not sp.is_absolute():
                sp = root / sp
            return sp
        except Exception:
            pass
    return root / "state" / "projects" / "PROJ-729-empirical-analysis-of-twin-prime-gaps-up.yaml"


def main() -> int:
    root = _project_root()
    artifacts = get_artifacts_to_hash()

    if not artifacts:
        print("ERROR: no artifacts found to hash; run the generation "
            "pipeline (code/generate_primes.py) first.", file=sys.stderr)
        return 1

    hashes: Dict[str, str] = {}
    manifest: Dict[str, Any] = {"generated_at": datetime.now(timezone.utc).isoformat(),
                                "artifacts": {}}
    for path in artifacts:
        if not Path(path).exists():
            print(f"Warning: {path} not found.", file=sys.stderr)
            continue
        h = compute_sha256(path)
        hashes[path] = h
        try:
            rel = str(Path(path).resolve().relative_to(root))
        except ValueError:
            rel = str(path)
        size = Path(path).stat().st_size
        manifest["artifacts"][rel] = {"sha256": h, "size_bytes": size}
        print(f"  {rel}: {h[:16]}... ({size} bytes)")

    if not hashes:
        print("ERROR: no hashable artifacts were readable.", file=sys.stderr)
        return 1

    state_path = _resolve_state_path()
    update_state_file(state_path, hashes, {
        "last_hashed": datetime.now(timezone.utc).isoformat(),
        "task": "T016",
    })
    print(f"State updated at {state_path}")

    # Durable copy of the hash manifest outside gitignored data caches.
    durable_dir = root / "results"
    durable_dir.mkdir(parents=True, exist_ok=True)
    durable_path = durable_dir / "artifact_hashes.json"
    with open(durable_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(f"Hash manifest written to {durable_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())