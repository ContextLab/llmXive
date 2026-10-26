"""
Script to recompute SHA‑256 checksums for the synthetic data files
(`tasks.json` and `skills.json`) and overwrite the project‑owned
`data/raw/checksums.json` file.

The script resolves file locations relative to the project root
(`paths.root`) and accepts optional command‑line arguments so that it
can be invoked both programmatically (e.g. from tests) and from the
quick‑start guide.

Usage:
    python code/write_checksums.py                # uses default locations
    python code/write_checksums.py <tasks> <skills>  # explicit paths
"""
import argparse
import json
import hashlib
import logging
from pathlib import Path

from llmxive_toolkit import paths

# Configure a simple console logger (no file handlers, no platform‑owned paths)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

def get_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a file in a memory‑efficient way.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to the file whose digest should be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256_hash = hashlib.sha256()
    # Read the file in small chunks to avoid loading large files into memory.
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _resolve_default_paths() -> tuple[Path, Path, Path]:
    """
    Resolve the default locations for tasks, skills and the checksum file
    based on the project root.
    """
    project_root = Path(paths.root)

    tasks_path = project_root / "data" / "raw" / "tasks.json"
    skills_path = project_root / "data" / "raw" / "skills.json"
    checksums_path = project_root / "data" / "raw" / "checksums.json"

    return tasks_path, skills_path, checksums_path


def _parse_cli() -> argparse.Namespace:
    """
    Parse optional positional arguments for the two source JSON files.
    If omitted, defaults derived from the project layout are used.
    """
    parser = argparse.ArgumentParser(
        description="Re‑compute SHA‑256 checksums for synthetic data files."
    )
    parser.add_argument(
        "tasks_file",
        nargs="?",
        help="Path to tasks.json (default: data/raw/tasks.json)",
    )
    parser.add_argument(
        "skills_file",
        nargs="?",
        help="Path to skills.json (default: data/raw/skills.json)",
    )
    return parser.parse_args()


def main() -> None:
    """
    Re‑compute the SHA‑256 checksums for the synthetic data files
    (`tasks.json` and `skills.json`) and overwrite
    ``data/raw/checksums.json`` with the fresh mapping.

    This script writes only to project‑owned locations under ``data/``.
    It deliberately does **not** touch any platform‑owned ``state/`` paths.
    """
    args = _parse_cli()

    # Resolve default locations
    default_tasks, default_skills, checksums_path = _resolve_default_paths()

    # Use CLI arguments if supplied, otherwise fall back to defaults
    tasks_path = Path(args.tasks_file) if args.tasks_file else default_tasks
    skills_path = Path(args.skills_file) if args.skills_file else default_skills

    # Verify that the source files exist; fail loudly if they do not.
    if not tasks_path.is_file():
        log.error(f"Missing tasks file: {tasks_path}")
        raise FileNotFoundError(f"Required file not found: {tasks_path}")

    if not skills_path.is_file():
        log.error(f"Missing skills file: {skills_path}")
        raise FileNotFoundError(f"Required file not found: {skills_path}")

    log.info(f"Computing SHA‑256 checksums for {tasks_path} and {skills_path}")

    # Compute the digests.
    checksums = {
        "tasks_json_sha256": get_sha256(tasks_path),
        "skills_json_sha256": get_sha256(skills_path),
    }

    # Write the mapping to the project‑owned JSON file.
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    checksums_path.write_text(
        json.dumps(checksums, indent=2, sort_keys=True), encoding="utf-8"
    )

    log.info(f"Checksums successfully written to {checksums_path}")
    # Echo the mapping for interactive runs.
    print(json.dumps(checksums, indent=2))


if __name__ == "__main__":
    main()
