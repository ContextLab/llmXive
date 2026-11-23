"""
create_layout.py

Script to create the required top‑level directory layout for the project
and write a plain‑text manifest (`data/dir_structure.txt`) listing the
nine expected directories.

The script is idempotent: running it multiple times will not raise errors
and will always produce the same manifest file.
"""

from pathlib import Path
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Define the list of directories that must exist (relative to the project
# root).  These are the nine directories required by task T001.
# ----------------------------------------------------------------------
REQUIRED_DIRS = [
    Path("code"),
    Path("code") / "simulation",
    Path("code") / "analysis",
    Path("code") / "utils",
    Path("tests") / "unit",
    Path("tests") / "integration",
    Path("data") / "raw",
    Path("data") / "processed",
    Path("data") / "processed" / "plots",
]

# ----------------------------------------------------------------------
# Helper to ensure a directory exists using the project's path helpers.
# Using `paths.<folder>` guarantees the folder is created inside the
# project‑owned area and not under the platform‑owned `state/` tree.
# ----------------------------------------------------------------------
def ensure_dir(dir_path: Path) -> Path:
    """
    Ensure that *dir_path* exists inside the project root.

    Returns the absolute Path object for convenience.
    """
    # The `paths` helper creates the parent folder if needed.
    # We resolve the appropriate top‑level helper based on the first part.
    top_folder = dir_path.parts[0]
    sub_parts = dir_path.parts[1:]

    # Dispatch to the correct `paths` function.
    if top_folder == "code":
        base = paths.code()
    elif top_folder == "tests":
        base = paths.tests()
    elif top_folder == "data":
        base = paths.data()
    else:
        raise ValueError(f"Unexpected top‑level folder: {top_folder}")

    target = base.joinpath(*sub_parts) if sub_parts else base
    target.mkdir(parents=True, exist_ok=True)
    return target

# ----------------------------------------------------------------------
# Main routine: create directories and write the manifest file.
# ----------------------------------------------------------------------
def main() -> None:
    # 1️⃣ Ensure all required directories exist.
    for d in REQUIRED_DIRS:
        ensure_dir(d)

    # 2️⃣ Write the manifest file under `data/dir_structure.txt`.
    manifest_path = paths.data("dir_structure.txt")
    # The manifest contains one directory per line, exactly as required.
    with manifest_path.open("w", encoding="utf-8") as f:
        for d in REQUIRED_DIRS:
            f.write(str(d) + "\n")

    print(f"Created {len(REQUIRED_DIRS)} directories and wrote manifest to {manifest_path}")

if __name__ == "__main__":
    main()
