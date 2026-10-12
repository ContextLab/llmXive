import logging
import os
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_DIRS = [
    "src",
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "output",
    "output/figures",
    "output/temporal_profiles",
    "contracts",
    "logs",
]


def create_directories():
    """Create the required project directory tree."""
    logger.info("Creating project directory structure...")
    for dir_path in REQUIRED_DIRS:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/Verified: {dir_path}")


def write_tree_snapshot(root_path: Path, output_file: Path):
    """
    Capture a filesystem snapshot.
    Attempts to use the system 'tree' command; falls back to a Python
    implementation if 'tree' is not installed.
    """
    logger.info(f"Capturing filesystem snapshot to {output_file}...")

    # Try using the system 'tree' command as requested in tasks.md
    try:
        # -a: all files, -L 3: depth 3
        result = subprocess.run(
            ["tree", "-a", "-L", "3"],
            cwd=root_path,
            capture_output=True,
            text=True,
            check=True,
        )
        snapshot = result.stdout
        logger.info("Used system 'tree' command for snapshot.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(
            "System 'tree' command not found or failed. Using Python fallback."
        )
        snapshot = _python_tree_fallback(root_path, max_depth=3)

    # Ensure logs directory exists before writing
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(snapshot, encoding="utf-8")
    logger.info("Snapshot written successfully.")


def _python_tree_fallback(root: Path, max_depth: int = 3) -> str:
    """Pure Python implementation of tree -a -L <depth>."""
    lines = []

    def walk(current_path: Path, depth: int):
        if depth > max_depth:
            return

        try:
            # Sort to ensure deterministic output
            items = sorted(current_path.iterdir(), key=lambda x: x.name)
        except PermissionError:
            return

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            prefix = "└── " if is_last else "├── "
            indent = "    " * (depth - 1) if depth > 0 else ""

            # Add trailing slash for directories to help grep verification
            suffix = "/" if item.is_dir() else ""
            lines.append(f"{indent}{prefix}{item.name}{suffix}")

            if item.is_dir():
                walk(item, depth + 1)

    lines.append(f".")
    walk(root, 1)
    return "\n".join(lines)


def main():
    """Main entry point for project scaffolding."""
    root = Path.cwd()

    # 1. Create directories
    create_directories()

    # 2. Capture snapshot
    snapshot_file = root / "logs" / "structure.txt"
    write_tree_snapshot(root, snapshot_file)

    # Final verification check (internal)
    if not snapshot_file.exists() or snapshot_file.stat().st_size == 0:
        logger.error("Verification failed: logs/structure.txt is missing or empty.")
        exit(1)

    logger.info("T001: Project structure created and snapshot captured.")


if __name__ == "__main__":
    main()
