"""
Setup script for creating the required top‑level directory layout
and writing the manifest file ``data/dir_structure.txt``.

The CI verification expects:
  1. All nine directories to exist on disk.
  2. ``data/dir_structure.txt`` to list those directories (one per line).

Running this script (``python -m code.setup_dir_structure``) creates the
directories using the project‑owned ``llmxive_toolkit.paths`` helpers and
overwrites the manifest with the canonical list.
"""

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _ensure_dir(*parts):
    """Create a directory (and any missing parents) under the project root."""
    p = paths.path(*parts)
    p.mkdir(parents=True, exist_ok=True)
    log.debug(f"Ensured directory: {p}")
    return p


def main() -> None:
    """
    Create the required directory tree and write the manifest.

    Expected layout (relative to the project root):
        code/
        code/simulation/
        code/analysis/
        code/utils/
        tests/unit/
        tests/integration/
        data/raw/
        data/processed/
        data/processed/plots/
    """
    # Define the directory hierarchy as tuples of path components.
    dirs = [
        ("code",),
        ("code", "simulation"),
        ("code", "analysis"),
        ("code", "utils"),
        ("tests", "unit"),
        ("tests", "integration"),
        ("data", "raw"),
        ("data", "processed"),
        ("data", "processed", "plots"),
    ]

    # Create each directory.
    for parts in dirs:
        _ensure_dir(*parts)

    # Write the manifest file.
    manifest_path = paths.data("dir_structure.txt")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        for parts in dirs:
            # Join with '/' to match the original manifest format.
            line = "/".join(parts)
            f.write(f"{line}\n")
    log.info(f"Directory layout created and manifest written to {manifest_path}")


if __name__ == "__main__":
    main()