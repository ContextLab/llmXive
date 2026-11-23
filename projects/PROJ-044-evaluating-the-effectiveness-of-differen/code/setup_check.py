"""T001: Setup verification for PROJ-044.

Verifies that the core scientific dependencies are importable, that the
heavy federated-learning dependencies (torch, opacus, datasets, pyarrow)
are declared in requirements.txt and importable when installed, and that
the project directory structure (data/, results/, figures/, logs/,
code/ subpackages) exists — creating any missing directories.

Exit code 0 = setup OK (core dependencies importable, structure present).
Exit code 1 = a core dependency is missing (install requirements.txt).
"""
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories required by the project structure in plan.md
REQUIRED_DIRS = [
    Path("data/raw"),
    Path("data/partitions"),
    Path("results"),
    Path("figures"),
    Path("logs"),
    Path("code/data"),
    Path("code/models"),
    Path("code/training"),
    Path("code/analysis"),
    Path("tests/unit"),
    Path("tests/integration"),
]

# Core dependencies that must be importable for the analysis stack.
CORE_DEPS = ["numpy", "pandas", "scipy", "statsmodels", "matplotlib"]

# Heavy FL dependencies: declared in requirements.txt; warned (not fatal)
# here because they are installed from requirements.txt in the run-book
# setup step and may be absent in a bare environment before `pip install`.
FL_DEPS = ["torch", "opacus", "datasets", "pyarrow"]

# Every dependency mandated by T001, checked against requirements.txt.
REQUIRED_IN_MANIFEST = [
    "torch", "opacus", "datasets", "pandas", "scipy", "statsmodels",
    "pyarrow",
]


def check_manifest() -> None:
    """Verify requirements.txt declares every mandated dependency."""
    manifest = PROJECT_ROOT / "requirements.txt"
    if not manifest.exists():
        print("FAIL: requirements.txt not found at project root")
        sys.exit(1)
    text = manifest.read_text().lower()
    missing = [d for d in REQUIRED_IN_MANIFEST if d not in text]
    if missing:
        print(f"FAIL: requirements.txt is missing: {missing}")
        sys.exit(1)
    print("OK: requirements.txt declares all mandated dependencies "
          "(torch, opacus, datasets, pandas, scipy, statsmodels, pyarrow)")


def check_imports() -> None:
    """Import-check core deps (fatal) and FL deps (warning only)."""
    failed = []
    for dep in CORE_DEPS:
        try:
            importlib.import_module(dep)
            print(f"OK: core dependency '{dep}' importable")
        except ImportError:
            print(f"FAIL: core dependency '{dep}' is NOT importable")
            failed.append(dep)
    for dep in FL_DEPS:
        try:
            importlib.import_module(dep)
            print(f"OK: federated-learning dependency '{dep}' importable")
        except ImportError:
            print(f"WARNING: '{dep}' not importable in this environment; "
                f"it is declared in requirements.txt — run "
                f"'pip install -r requirements.txt' before training")
    if failed:
        print(f"Setup check FAILED: missing core dependencies {failed}")
        sys.exit(1)


def check_structure() -> None:
    """Create and verify the project directory structure."""
    for rel in REQUIRED_DIRS:
        d = PROJECT_ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        if not d.is_dir():
            print(f"FAIL: could not create directory {d}")
            sys.exit(1)
    print(f"OK: project structure present under {PROJECT_ROOT} "
          "(data/raw, data/partitions, results, figures, logs, "
          "code/*, tests/*)")


def main() -> int:
    print(f"=== PROJ-044 setup check (project root: {PROJECT_ROOT}) ===")
    check_manifest()
    check_structure()
    check_imports()
    print("=== Setup check PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
