"""Setup directory structure for data/raw and data/processed.

Ensures the required data directories exist before data processing
begins. Creates .gitkeep placeholder files so the (otherwise empty)
directories are tracked by version control.
"""

import os
import sys
from pathlib import Path

# Allow running as a script from the code/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_config_from_args  # noqa: E402
from utils.logger import get_logger  # noqa: E402


def main():
    """Create data/raw and data/processed directories with evidence files."""
    config = get_config_from_args()
    logger = get_logger("scripts.setup_data_dirs")

    # Project root is two levels above code/scripts/.
    project_root = Path(__file__).resolve().parents[2]

    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    created = []
    for d in (raw_dir, processed_dir):
        existed = d.exists()
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("")
        created.append((str(d), existed))

    # Write a manifest documenting the created structure (evidence artifact).
    manifest_path = processed_dir / ".directory_structure.txt"
    lines = [
        "Data directory structure for PROJ-277-predicting-oxidation-resistance",
        f"Created by: {Path(__file__).name}",
        "",
    ]
    for path, existed in created:
        state = "already existed" if existed else "created"
        lines.append(f"{path} [{state}]")
    lines.append("")
    lines.append("Contents of data/:")
    for p in sorted((project_root / "data").rglob("*")):
        lines.append(f"  {p.relative_to(project_root)}")
    manifest_path.write_text("\n".join(lines) + "\n")

    logger.info("Data directories ready: %s, %s", raw_dir, processed_dir)
    logger.info("Structure manifest written to %s", manifest_path)

    print(f"OK raw_dir={raw_dir}")
    print(f"OK processed_dir={processed_dir}")
    print(f"OK manifest={manifest_path}")


if __name__ == "__main__":
    main()