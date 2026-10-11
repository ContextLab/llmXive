"""T001: Establish the project layout.

Creates the canonical directory structure required by the project:
code/, data/raw/, data/processed/, data/derived/, tests/unit,
tests/contract, tests/integration, specs/, logs/, and
specs/001-neural-entropy-cognitive-flexibility/contracts/.

Each data/test directory receives a .gitkeep file so the (otherwise
empty) directories are tracked by git. Also verifies that every
dependency pinned in requirements.txt is importable in the current
environment and writes the outcome to logs/setup_check.txt.
"""
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "code",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/derived",
    "tests",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "specs",
    "specs/001-neural-entropy-cognitive-flexibility",
    "specs/001-neural-entropy-cognitive-flexibility/contracts",
    "logs",
]

# requirements.txt pins, mapped to import names where they differ
IMPORT_NAMES = {
    "MNE": "mne",
    "statsmodels": "statsmodels",
    "numpy": "numpy",
    "pandas": "pandas",
    "PyYAML": "yaml",
    "requests": "requests",
    "scikit-learn": "sklearn",
    "numba": "numba",
    "jsonschema": "jsonschema",
    "huggingface_hub": "huggingface_hub",
    "psutil": "psutil",
}


def create_layout() -> None:
    for rel in DIRECTORIES:
        d = PROJECT_ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        print(f"ready: {d.relative_to(PROJECT_ROOT)}")


def check_requirements() -> bool:
    req = PROJECT_ROOT / "requirements.txt"
    if not req.exists():
        print("requirements.txt missing", file=sys.stderr)
        return False
    all_ok = True
    lines = []
    for raw in req.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pkg = line.split("==")[0].split(">=")[0].strip()
        mod = IMPORT_NAMES.get(pkg, pkg)
        try:
            importlib.import_module(mod)
            lines.append(f"OK    {line} (import {mod})")
        except ImportError as exc:
            all_ok = False
            lines.append(f"FAIL  {line} (import {mod}): {exc}")
    report = "\n".join(lines)
    print(report)
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "setup_check.txt").write_text(report + "\n", encoding="utf-8")
    return all_ok


def main() -> int:
    create_layout()
    ok = check_requirements()
    print("Project layout established.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
