"""Create the canonical project directory tree and structure report (T001).

Creates the directories required by the project plan, ensures package
__init__.py files exist, and writes results/structure_report.txt listing
every directory in the project tree (sorted), mirroring:
    find . -type d | sort > results/structure_report.txt
"""
from pathlib import Path

from llmxive_toolkit import paths

ROOT = Path(paths.root)

CANONICAL_DIRS = [
    "code",
    "code/data",
    "code/models",
    "code/evaluation",
    "code/utils",
    "code/scripts",
    "tests",
    "data/raw",
    "data/processed",
    "data/external",
    "results",
    "logs",
    "specs/001-predicting-molecular-properties",
]

PACKAGE_DIRS = [
    "code",
    "code/data",
    "code/models",
    "code/evaluation",
    "code/utils",
    "code/scripts",
    "tests",
]


def create_tree() -> None:
    """Create every canonical directory and package __init__.py."""
    for rel in CANONICAL_DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)
    for rel in PACKAGE_DIRS:
        init = ROOT / rel / "__init__.py"
        if not init.exists():
            init.write_text(
                '"""Package initializer for the molecular properties pipeline."""\n',
                encoding="utf-8",
            )


def write_structure_report() -> Path:
    """Write the sorted directory listing to results/structure_report.txt."""
    dirs = sorted(
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*")
        if p.is_dir() and ".git" not in p.parts
    )
    report_path = paths.results("structure_report.txt")
    report_path.write_text("\n".join(dirs) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    create_tree()
    report = write_structure_report()
    missing = [d for d in CANONICAL_DIRS if not (ROOT / d).is_dir()]
    if missing:
        raise RuntimeError(f"Missing canonical directories: {missing}")
    print(f"Structure report written to {report}")
    for d in CANONICAL_DIRS:
        print(f"OK {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())