"""T001: Establish the authoritative project layout and record an
environment snapshot proving the pinned dependencies from
code/pyproject.toml are installed and importable.

Idempotent: safe to re-run. Creates the directory tree required by the
task verification:

    code/{data,analysis,viz,lib,utils,reporting}
    data/{raw,processed,results}
    docs/ contracts/ tests/{unit,integration,contract}

and writes docs/install_log.txt (the install/environment evidence).
"""
import sys
import platform
from datetime import datetime, timezone
from pathlib import Path
from importlib import metadata

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "code/data",
    "code/analysis",
    "code/viz",
    "code/lib",
    "code/utils",
    "code/reporting",
    "data/raw",
    "data/processed",
    "data/results",
    "docs",
    "contracts",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

# Dependencies pinned in code/pyproject.toml (plus the platform-provided
# scientific stack the analysis relies on).
PINNED_DEPENDENCIES = [
    "pandas",
    "numpy",
    "scipy",
    "scikit-learn",
    "statsmodels",
    "matplotlib",
    "seaborn",
    "requests",
    "pyyaml",
    "jsonschema",
    "pydantic",
    "pytest",
]

def ensure_layout() -> None:
    """Create every required directory and a .gitkeep placeholder."""
    for rel in DIRECTORIES:
        d = PROJECT_ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not any(p for p in d.iterdir() if p.name != ".gitkeep"):
            keep.touch()
    print("Directory layout verified:")
    for rel in DIRECTORIES:
        print(f"  {rel}/")

def snapshot_environment() -> Path:
    """Record installed versions of the pinned dependencies.

    Writes docs/install_log.txt with the resolved version of every
    dependency declared in code/pyproject.toml (plus the scientific
    stack), failing loudly if any declared dependency is missing.
    """
    lines = [
        "# Install / environment snapshot (T001)",
        f"generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"python: {sys.version.split()[0]} ({platform.python_implementation()})",
        f"platform: {platform.platform()}",
        "manifest: code/pyproject.toml (authoritative project config)",
        "",
        "# Resolved dependency versions",
    ]
    missing = []
    for dep in PINNED_DEPENDENCIES:
        try:
            version = metadata.version(dep)
        except metadata.PackageNotFoundError:
            missing.append(dep)
            version = "NOT INSTALLED"
        lines.append(f"{dep}=={version}")
        print(f"  {dep}=={version}")
    if missing:
        raise RuntimeError(
            "Pinned dependencies not installed: "
            + ", ".join(missing)
            + ". Run: pip install -r requirements.txt"
        )
    lines += [
        "",
        "# Import check",
        "import pandas, numpy, scipy, statsmodels, matplotlib, requests OK"
        if _import_check()
        else "IMPORT CHECK FAILED",
    ]
    out = PROJECT_ROOT / "docs" / "install_log.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Environment snapshot written to {out}")
    return out

def _import_check() -> bool:
    try:
        import pandas  # noqa: F401
        import numpy  # noqa: F401
        import scipy  # noqa: F401
        import statsmodels  # noqa: F401
        import matplotlib  # noqa: F401
        import requests  # noqa: F401
    except Exception as exc:  # pragma: no cover - loud failure path
        print(f"Import check failed: {exc}")
        return False
    return True

def main() -> None:
    print(f"Project root: {PROJECT_ROOT}")
    ensure_layout()
    snapshot_environment()
    print("T001 setup complete.")

if __name__ == "__main__":
    main()
