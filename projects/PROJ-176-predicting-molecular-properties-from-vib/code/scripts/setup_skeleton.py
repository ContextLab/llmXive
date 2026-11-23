"""Create the canonical project skeleton for T001.

Actions:
1. Create the required directory tree.
2. Ensure every package directory has an EMPTY ``__init__.py``.
3. Run ``python -m compileall code/`` and fail loudly on any error.
4. Write a sorted directory listing to ``results/structure_report.txt``
   and assert every expected directory is present in it.
"""
import compileall
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root

EXPECTED_DIRS = [
    "code",
    "code/data",
    "code/evaluation",
    "code/models",
    "code/scripts",
    "code/utils",
    "data/external",
    "data/processed",
    "data/raw",
    "logs",
    "results",
    "specs/001-predict-molecular-properties",
    "specs/001-predict-molecular-properties/contracts",
    "tests",
]

PACKAGE_DIRS = [
    "code",
    "code/data",
    "code/evaluation",
    "code/models",
    "code/scripts",
    "code/utils",
    "tests",
]


def create_directories() -> None:
    for rel in EXPECTED_DIRS:
        (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)


def ensure_empty_init_files() -> None:
    """Overwrite every package __init__.py with a truly empty file."""
    for rel in PACKAGE_DIRS:
        init_path = PROJECT_ROOT / rel / "__init__.py"
        init_path.write_bytes(b"")
        assert init_path.read_bytes() == b"", f"{init_path} is not empty"


def run_compileall() -> None:
    """Compile every .py file under code/; raise on failure."""
    ok = compileall.compile_dir(
        str(PROJECT_ROOT / "code"), quiet=1, force=True
    )
    if not ok:
        raise RuntimeError("python -m compileall code/ reported errors")
    # Also run the exact verification command from tasks.md.
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "code"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "python -m compileall code/ exited non-zero: "
            + proc.stderr.strip()
        )


def write_structure_report() -> Path:
    """Equivalent of: find . -type d | sort > results/structure_report.txt"""
    dirs = sorted(
        str(p.relative_to(PROJECT_ROOT))
        for p in PROJECT_ROOT.rglob("*")
        if p.is_dir()
        and ".git" not in p.parts
        and "__pycache__" not in p.parts
    )
    report_path = paths.results("structure_report.txt")
    report_path.write_text("\n".join(dirs) + "\n")
    return report_path


def verify_report(report_path: Path) -> None:
    listed = set(report_path.read_text().splitlines())
    missing = [d for d in EXPECTED_DIRS if d not in listed]
    if missing:
        raise RuntimeError(
            "structure_report.txt is missing expected directories: "
            + ", ".join(missing)
        )


def main() -> int:
    create_directories()
    ensure_empty_init_files()
    run_compileall()
    report_path = write_structure_report()
    verify_report(report_path)
    print(f"structure report written to {report_path}")
    print("python -m compileall code/ exited 0")
    print("all __init__.py files are empty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
