"""SHA-256 checksum generation and state recording for the DEAP-EMG dataset.

Implements task T005b (FR-001 part 2, Constitution Principle III & V):
computes SHA-256 checksums for every file under ``data/raw`` and records
them in the project state file
``state/projects/PROJ-214-decoding-emotional-valence-from-facial-e.yaml``
under the ``artifact_hashes`` key.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from llmxive_toolkit import paths

from config import ensure_directories
from state_manager import load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("checksum_manager")

STATE_RELATIVE_PATH = Path(
    "state/projects/PROJ-214-decoding-emotional-valence-from-facial-e.yaml"
)
CHUNK_SIZE = 1024 * 1024  # 1 MiB


def _state_path() -> Path:
    return paths.root / STATE_RELATIVE_PATH


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Cannot hash missing file: {file_path}")
    digest = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate_dataset_checksums(data_dir: Path) -> Dict[str, str]:
    """Generate checksums for all files in the raw data directory.

    Args:
        data_dir: Path to the directory containing dataset files.

    Returns:
        Dictionary mapping relative file paths (POSIX style, relative to
        ``data_dir``) to their SHA-256 checksums.
    """
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise NotADirectoryError(f"Raw data directory not found: {data_dir}")

    checksums: Dict[str, str] = {}
    for file_path in sorted(data_dir.rglob("*")):
        if file_path.is_file():
            rel = file_path.relative_to(data_dir).as_posix()
            checksums[rel] = calculate_sha256(file_path)
            log.info("SHA-256 %s -> %s", rel, checksums[rel])

    if not checksums:
        raise RuntimeError(
              f"No dataset files found in {data_dir}. "
              "Run code/download.py (T005a) before generating checksums."
        )
    return checksums


def _load_state_flexible() -> Dict:
    """Load the state file via state_manager, tolerating signature variants."""
    try:
        return load_state()
    except TypeError:
        return load_state(_state_path())


def _save_state_flexible(state: Dict) -> None:
    """Save the state file via state_manager, tolerating signature variants."""
    try:
        save_state(state)
    except TypeError:
        save_state(_state_path(), state)


def update_state_with_checksums(checksums: Dict[str, str]) -> bool:
    """Update the project state file with dataset checksums.

    Args:
        checksums: Dictionary of file paths to checksums.

    Returns:
        True if successful, False otherwise.
    """
    if not checksums:
        raise ValueError("Refusing to record an empty checksum set.")

    state_path = _state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)

    state = _load_state_flexible()
    if not isinstance(state, dict):
        raise TypeError(
            f"State file {state_path} did not yield a dict "
            f"(got {type(state).__name__})."
        )

    hashes = state.setdefault("artifact_hashes", {})
    if not isinstance(hashes, dict):
        raise TypeError(
            f"'artifact_hashes' in {state_path} is not a mapping "
            f"(got {type(hashes).__name__})."
        )
    hashes.update(checksums)
    state["artifact_hashes_updated_at"] = datetime.now(timezone.utc).isoformat()

    _save_state_flexible(state)
    log.info(
        "Recorded %d checksum(s) under 'artifact_hashes' in %s",
        len(checksums),
        state_path,
    )
    return True


def validate_existing_checksums() -> Dict[str, bool]:
    """Validate existing checksums in the state file against current files.

    Returns:
        Dictionary mapping file paths to validation status (True if valid).
    """
    state = _load_state_flexible()
    hashes = state.get("artifact_hashes", {})
    if not hashes:
        raise RuntimeError(
            "No 'artifact_hashes' entries found in the state file; "
            "run checksum generation first."
        )

    raw_dir = paths.data("raw")
    results: Dict[str, bool] = {}
    for rel, expected in hashes.items():
        current = raw_dir / rel
        if not current.is_file():
            results[rel] = False
            log.warning("MISSING file for recorded checksum: %s", rel)
            continue
        actual = calculate_sha256(current)
        results[rel] = actual == expected
        if results[rel]:
            log.info("VALID   %s", rel)
        else:
            log.error(
                "INVALID %s (expected %s, got %s)", rel, expected, actual
            )
    return results


def main() -> None:
    """Main entry point for checksum generation and validation.

    Computes SHA-256 checksums for all files in ``data/raw``, records them
    in the project state file under ``artifact_hashes``, writes a JSON
    record to ``data/logs/checksums.json``, and re-validates the recorded
    checksums against the files on disk.
    """
    ensure_directories()

    raw_dir = paths.data("raw")
    log.info("Generating SHA-256 checksums for files under %s", raw_dir)
    checksums = generate_dataset_checksums(raw_dir)

    update_state_with_checksums(checksums)

    # Machine-readable log of the recorded checksums (data/logs/).
    record = {
        "algorithm": "sha256",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_dir": str(raw_dir),
        "n_files": len(checksums),
        "checksums": checksums,
    }
    log_path = paths.data("logs", "checksums.json")
    with open(log_path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
    log.info("Wrote checksum record to %s", log_path)

    # Immediately re-validate to prove the recorded hashes match disk.
    results = validate_existing_checksums()
    invalid = [rel for rel, ok in results.items() if not ok]
    if invalid:
        raise RuntimeError(
            "Checksum validation failed for: " + ", ".join(invalid)
        )
    log.info(
        "All %d recorded checksum(s) validated successfully.", len(results)
    )


if __name__ == "__main__":
    main()
