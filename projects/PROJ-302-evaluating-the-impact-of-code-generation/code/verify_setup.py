"""Setup verification for T001.

Checks that:
1. The project skeleton directories exist (code/, data/, tests/, docs/).
2. requirements.txt pins every required package (including statsmodels).
3. Every pinned dependency can be imported (installing any missing one
   via pip so the environment matches requirements.txt).

Writes evidence to results/setup_verification.json and exits 0 on success.
"""

import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Every package the spec/plan requires, mapped to its import name.
REQUIRED_PACKAGES = {
    "datasets": "datasets",
    "scikit-learn": "sklearn",
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "statsmodels": "statsmodels",
    "radon": "radon",
    "torch": "torch",
    "transformers": "transformers",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "pyyaml": "yaml",
    "requests": "requests",
    "gitpython": "git",
    "pytest": "pytest",
    "ruff": "ruff",
    "black": "black",
    "pyarrow": "pyarrow",
    "codecarbon": "codecarbon",
    "tenacity": "tenacity",
}

SKELETON_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/synthetic",
    "data/reports",
    "data/figures",
    "tests/unit",
    "tests/integration",
    "docs",
]

PIN_RE = re.compile(r"^[A-Za-z0-9_.\-]+==[0-9][A-Za-z0-9_.*\-]*$")


def parse_requirements(path: Path) -> dict:
    """Parse requirements.txt into {package: version}; fail loudly on bad lines."""
    if not path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {path}")
    pins = {}
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not PIN_RE.match(line):
            raise ValueError(
                f"requirements.txt line {lineno} is not an exact pin: {line!r}"
            )
        name, version = line.split("==", 1)
            # normalize to lowercase for lookup
        pins[name.lower().replace("_", "-")] = version
    return pins


def ensure_dirs() -> list:
    created = []
    for d in SKELETON_DIRS:
        p = paths.root / d
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


def import_or_install(package: str, import_name: str, version: str) -> dict:
    """Import a package; if missing, pip install the pinned version."""
    try:
        mod = importlib.import_module(import_name)
        installed_version = getattr(mod, "__version__", "unknown")
        return {
            "package": package,
            "status": "imported",
            "installed_version": installed_version,
            "pinned_version": version,
        }
    except ImportError:
        log.info("Package %s missing; installing pinned version %s", package, version)
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet",
             f"{package}=={version}"],
            capture_output=True, text=True, timeout=480,
        )
        if proc.returncode != 0:
            return {
                "package": package,
                "status": "install_failed",
                "pinned_version": version,
                "error": proc.stderr[-2000:],
            }
        mod = importlib.import_module(import_name)
        return {
            "package": package,
            "status": "installed_via_pip",
            "installed_version": getattr(mod, "__version__", "unknown"),
            "pinned_version": version,
        }


def main() -> int:
    root = paths.root
    req_path = root / "requirements.txt"

    # 1. Skeleton directories
    created = ensure_dirs()
    missing_dirs = [d for d in SKELETON_DIRS if not (root / d).is_dir()]
    if missing_dirs:
        raise RuntimeError(f"Skeleton directories missing: {missing_dirs}")

    # 2. requirements.txt pins
    pins = parse_requirements(req_path)
    unpinned = [p for p in REQUIRED_PACKAGES if p not in pins]
    if unpinned:
        raise RuntimeError(
            f"requirements.txt is missing required packages: {unpinned}"
        )

    # 3. Import (or install) every dependency
    results = []
    failures = []
    for package, import_name in REQUIRED_PACKAGES.items():
        try:
            res = import_or_install(package, import_name, pins[package])
        except Exception as exc:  # noqa: BLE001
            res = {
                "package": package,
                "status": "error",
                "pinned_version": pins[package],
                "error": str(exc),
            }
        results.append(res)
        if res["status"] not in ("imported", "installed_via_pip"):
            failures.append(res)

    report = {
        "task": "T001",
        "skeleton_directories": SKELETON_DIRS,
        "directories_created": created,
        "requirements_path": str(req_path),
        "all_required_packages_pinned": not unpinned,
        "package_results": results,
        "failures": failures,
        "success": not failures and not missing_dirs and not unpinned,
    }

    out = paths.results("setup_verification.json")
    out.write_text(json.dumps(report, indent=2))
    log.info("Setup verification report written to %s", out)

    if failures:
        for f in failures:
            log.error("Dependency failure: %s", f)
        return 1
    log.info("Setup verification PASSED: %d packages available, "
             "skeleton complete.", len(REQUIRED_PACKAGES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
