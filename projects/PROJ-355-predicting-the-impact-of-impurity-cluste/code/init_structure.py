"""Idempotently initialize the project directory structure (T001a).

Creates the project root and all required subdirectories:
code/, data/raw/, data/processed/, results/, tests/unit/, tests/integration/.
Safe to run repeatedly: existing directories are left untouched.
Writes a log of created directories to results/structure_init.log.
"""
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Return the project root (parent of the code/ directory)."""
    return Path(__file__).resolve().parent.parent


def init_structure(root: Path) -> list:
    """Create the required subdirectories under root, idempotently.

    Returns the list of directories that were newly created.
    """
    required = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "results",
        root / "tests" / "unit",
        root / "tests" / "integration",
    ]
    created = []
    for d in required:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


def main() -> int:
    root = get_project_root()
    created = init_structure(root)

    # Verify all required directories now exist.
    required = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration",
    ]
    missing = [r for r in required if not (root / r).is_dir()]
    if missing:
        print(f"ERROR: missing directories after init: {missing}", file=sys.stderr)
        return 1

    # Write an execution log for verification.
    log_path = root / "results" / "structure_init.log"
    with open(log_path, "w") as f:
        f.write(f"project_root: {root}\n")
        f.write("required_directories:\n")
        for r in required:
            f.write(f"  - {r}\n")
        f.write("newly_created:\n")
        if created:
            for c in created:
                f.write(f"  - {c.relative_to(root)}\n")
        else:
            f.write("  []  # all directories already existed (idempotent rerun)\n")
        f.write("status: OK\n")

    print(f"Project structure verified at {root}")
    print(f"Newly created: {[str(c.relative_to(root)) for c in created] or 'none (idempotent)'}")
    print(f"Log written to {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())