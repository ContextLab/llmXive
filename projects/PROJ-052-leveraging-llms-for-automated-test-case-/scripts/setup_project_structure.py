"""
Create the project structure per T001:
directories code/, specs/, data/, contracts/, tests/unit/, tests/integration/
and EMPTY __init__.py files in code/, tests/, tests/unit/, tests/integration/.
Running this script is idempotent; it verifies and reports each artifact.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "code",
    "specs",
    "data",
    "contracts",
    "tests/unit",
    "tests/integration",
]

# (path, must_be_empty)
INIT_FILES = [
    ("code/__init__.py", True),
    ("tests/__init__.py", True),
    ("tests/unit/__init__.py", True),
    ("tests/integration/__init__.py", True),
]


def main() -> int:
    failures = []

    for d in DIRECTORIES:
        path = PROJECT_ROOT / d
        path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            failures.append(f"directory not created: {d}")
        else:
            print(f"[OK] directory {d}/")

    for rel, must_be_empty in INIT_FILES:
        path = PROJECT_ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.stat().st_size != 0:
            # (Re)create as a truly EMPTY file per the task spec.
            with open(path, "wb") as f:
                f.write(b"")
        size = path.stat().st_size
        if must_be_empty and size != 0:
            failures.append(f"{rel} is not empty (size={size})")
        else:
            print(f"[OK] {rel} exists and is EMPTY (0 bytes)")

    if failures:
        for f_ in failures:
            print(f"[FAIL] {f_}", file=sys.stderr)
        return 1
    print("T001 project structure verified: all directories exist and all __init__.py files are empty.")
    return 0


if __name__ == "__main__":
    sys.exit(main())