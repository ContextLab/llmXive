"""
T001: Project setup verification for PROJ-044.

Responsibilities:
1. Install the project dependencies from requirements.txt into the
   active Python environment (idempotent; T001's mandate is to install
   torch, opacus, datasets, pandas, scipy, statsmodels, pyarrow).
2. Verify every required third‑party package is importable.
3. Create the canonical project directory structure (data/raw,
   data/partitions, results, figures).

Exits non‑zero with a clear message if any dependency cannot be
installed or imported — the failure is loud, never silent.
"""
import importlib
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

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

# Canonical directories from plan.md Project Structure. paths.* create
# the folder; we pass a dummy file name and use its parent directory.
REQUIRED_DIRS = [
    ("data/raw", paths.data("raw", ".keep").parent),
    ("data/partitions", paths.data("partitions", ".keep").parent),
    ("results", paths.results("raw_logs.csv").parent),
    ("figures", paths.figures(".keep").parent),
]


def install_dependencies() -> bool:
    """Install requirements.txt into the current interpreter's env.

    Returns True on success. Pinned versions in requirements.txt resolve the
    NumPy / pyarrow incompatibility observed in earlier runs.
    """
    req_path = paths.root / "requirements.txt"
    if not req_path.exists():
        log.error("requirements.txt not found at %s", req_path)
        return False

    log.info("Installing dependencies from %s ...", req_path)
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("pip install failed (rc=%d)", result.returncode)
        sys.stderr.write(result.stdout[-4000:] + "\n")
        sys.stderr.write(result.stderr[-4000:] + "\n")
        return False
    log.info("pip install completed successfully.")
    return True


def check_dependencies() -> int:
    """Import each required package; return the number of failures."""
    failures = 0
    for module_name, pip_name in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "unknown")
            print(f"  OK    {pip_name} ({module_name}) {version}")
        except ImportError as exc:
            failures += 1
            print(f"  FAIL  {pip_name}: {exc}", file=sys.stderr)
    return failures


def ensure_directories() -> None:
    """Create the canonical project directory structure."""
    for label, path in REQUIRED_DIRS:
        path.mkdir(parents=True, exist_ok=True)
        print(f"  DIR   {label} -> {path}")

    # Clean up any leftover placeholder *file* (not a directory).
    # The previous implementation attempted to unlink a directory,
    # which raised IsADirectoryError. We now guard against that.
    placeholder_path = paths.results(".placeholder")
    try:
        if placeholder_path.is_file():
            placeholder_path.unlink()
            print(f"  CLEAN placeholder file removed: {placeholder_path}")
    except Exception as e:
        # Non‑critical; log and continue.
        log.warning("Failed to clean placeholder file: %s", e)


def main() -> int:
    print("=== PROJ-044 setup check (T001) ===")
    print("Project root:", paths.root)

    print("\n[1/3] Installing dependencies from requirements.txt ...")
    if not install_dependencies():
        print(
            "\nSETUP INCOMPLETE: dependency installation failed. "
            "Inspect the pip output above.",
            file=sys.stderr,
        )
        return 1

    print("\n[2/3] Checking dependency imports ...")
    failures = check_dependencies()

    print("\n[3/3] Creating project directory structure ...")
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
