"""
Directory management utilities for the llmXive science pipeline.

Provides robust creation of project data directories with mkdir -p semantics.
"""
import os
import sys
from pathlib import Path


def ensure_data_directories(base_dir: Path | None = None) -> list[Path]:
    """
    Ensure the standard data directory structure exists under the project root.

    Creates:
      - data/raw/
      - data/processed/
      - data/results/

    Args:
        base_dir: The project root directory. If None, defaults to the parent
                  of this module's location (code/utils/..).

    Returns:
        A list of Path objects for the created directories.

    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    if base_dir is None:
        # Default to project root: code/utils/.. -> code/..
        base_dir = Path(__file__).resolve().parent.parent.parent

    data_root = base_dir / "data"
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results",
    ]

    created = []
    for dir_path in required_dirs:
        try:
            # parents=True ensures mkdir -p behavior
            dir_path.mkdir(parents=True, exist_ok=True)
            # Verify writability
            test_file = dir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            created.append(dir_path)
        except (OSError, PermissionError) as e:
            raise RuntimeError(
                f"Failed to create or verify write access for {dir_path}: {e}"
            ) from e

    return created


def main() -> int:
    """
    CLI entry point to ensure data directories exist.

    Usage:
        python -m utils.directories

    Returns:
        0 on success, non-zero on failure.
    """
    try:
        base = Path(__file__).resolve().parent.parent.parent
        dirs = ensure_data_directories(base)
        print(f"Successfully ensured data directories under: {base / 'data'}")
        for d in dirs:
            print(f"  - {d}")
        return 0
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
