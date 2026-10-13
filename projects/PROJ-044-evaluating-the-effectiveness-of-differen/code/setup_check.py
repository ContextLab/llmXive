"""
T001: Project setup verification for PROJ-044.

Verifies that all required third-party dependencies are importable,
creates the canonical project directory structure (data/raw,
data/partitions, results, figures), and prints a summary. Exits
non-zero with a clear message if any dependency is missing so the
failure is loud, never silent.
"""
import importlib
import sys

from llmxive_toolkit import paths

# Required dependencies per requirements.txt (T001).
REQUIRED_PACKAGES = [
    ("torch", "torch"),
    ("opacus", "opacus"),
    ("datasets", "datasets"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("statsmodels", "statsmodels"),
    ("matplotlib", "matplotlib"),
    ("pyarrow", "pyarrow"),
]

# Canonical directories from plan.md Project Structure.
REQUIRED_DIRS = [
    ("data/raw", paths.data("raw")),
    ("data/partitions", paths.data("partitions")),
    ("results", paths.results(".placeholder")),
    ("figures", paths.figures(".placeholder")),
]


def check_dependencies() -> int:
    """Import each required package; return the number of failures."""
    failures = 0
    for module_name, pip_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
            print(f"  OK    {pip_name} ({module_name})")
        except ImportError as exc:
            failures += 1
            print(f"  FAIL  {pip_name}: {exc}", file=sys.stderr)
    return failures


def ensure_directories() -> None:
    """Create the canonical project directory structure."""
    for label, path in REQUIRED_DIRS:
        # paths.* already creates the folder; strip placeholder file.
        if path.name == ".placeholder":
            placeholder = path
            if placeholder.exists():
                placeholder.unlink()
            print(f"  DIR   {label} -> {path.parent}")
        else:
            print(f"  DIR   {label} -> {path}")


def main() -> int:
    print("=== PROJ-044 setup check (T001) ===")
    print("Project root:", paths.root)

    print("\n[1/2] Checking dependencies from requirements.txt ...")
    failures = check_dependencies()

    print("\n[2/2] Creating project directory structure ...")
    ensure_directories()

    if failures:
        print(
            f"\nSETUP INCOMPLETE: {failures} dependency(ies) missing. "
            "Run: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    print("\nSETUP OK: all dependencies importable, directories ready.")
    print("Runnable entry point: python code/main.py (see quickstart.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
