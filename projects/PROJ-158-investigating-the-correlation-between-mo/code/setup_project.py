"""Create the project directory structure and initialize __init__.py files.

Creates the following directories (relative to the project root):
- code/data, code/models, code/analysis, code/utils
- data/raw, data/processed
- results, tests

And adds empty __init__.py files to each code/ subdirectory.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root

CODE_SUBDIRS = ["data", "models", "analysis", "utils"]
DATA_SUBDIRS = ["raw", "processed"]
TOP_LEVEL_DIRS = ["results", "tests"]


def main() -> None:
    created_dirs = []
    init_files = []

    # code/ subdirectories with __init__.py
    for sub in CODE_SUBDIRS:
        d = PROJECT_ROOT / "code" / sub
        d.mkdir(parents=True, exist_ok=True)
        created_dirs.append(d)
        init_path = d / "__init__.py"
        if not init_path.exists():
            init_path.write_text("")
        init_files.append(init_path)

    # data/ subdirectories
    for sub in DATA_SUBDIRS:
        d = PROJECT_ROOT / "data" / sub
        d.mkdir(parents=True, exist_ok=True)
        created_dirs.append(d)

    # top-level directories
    for name in TOP_LEVEL_DIRS:
        d = PROJECT_ROOT / name
        d.mkdir(parents=True, exist_ok=True)
        created_dirs.append(d)

    # Report the resulting structure as evidence
    print("Project structure created under:", PROJECT_ROOT)
    for d in created_dirs:
        print(f"  DIR  {d.relative_to(PROJECT_ROOT)}")
    for f in init_files:
        print(f"  INIT {f.relative_to(PROJECT_ROOT)}")

    # Verify everything exists
    missing = [d for d in created_dirs if not d.is_dir()]
    missing += [f for f in init_files if not f.is_file()]
    if missing:
        print("ERROR: missing expected paths:", missing, file=sys.stderr)
        sys.exit(1)
    print("All required directories and __init__.py files verified.")


if __name__ == "__main__":
    main()