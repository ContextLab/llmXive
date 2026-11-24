"""
T001 setup script: creates the full project skeleton (all required
directories), verifies that importing the ``code`` package configures a
project-wide logger, and runs a dummy function decorated with
``@limit_resources`` so that ``data/resource_usage.json`` is written with
the keys ``runtime_seconds`` and ``peak_ram_gb``.

Usage:
    python code/setup_skeleton.py
"""

import json
import sys
import time
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

# Make sibling modules (resource_monitor) importable
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Directories required by T001
REQUIRED_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "artifacts" / "models",
    PROJECT_ROOT / "artifacts" / "metrics",
    PROJECT_ROOT / "artifacts" / "reports",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "tests" / "unit",
    PROJECT_ROOT / "tests" / "integration",
    PROJECT_ROOT / "specs" / "001-predicting-the-influence-of-alloying-on" / "contracts",
    PROJECT_ROOT / "logs",
]


def create_directories() -> None:
    """Create every directory required by the T001 verification."""
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        print(f"[ok] directory exists: {d.relative_to(PROJECT_ROOT)}")


def verify_code_package_logger() -> logging.Logger:
    """Import the ``code`` package and confirm it exposes a logger."""
    # Ensure the project root is first on sys.path so the local ``code``
    # package shadows the stdlib ``code`` module.
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    import code as code_pkg  # local package (project root is first on sys.path)
    assert hasattr(code_pkg, "logger"), "code package does not expose a logger"
    assert isinstance(code_pkg.logger, logging.Logger)
    print(f"[ok] importing 'code' produced logger: {code_pkg.logger.name}")
    return code_pkg.logger


def run_dummy_decorated_function() -> dict:
    """Run a dummy function wrapped with @limit_resources and return the
    JSON usage report it writes to data/resource_usage.json."""
    from resource_monitor import limit_resources

    @limit_resources()
    def dummy_workload():
        # A small, real computation so the measured runtime is genuine.
        total = 0.0
        for i in range(200000):
            total += float(i) * 0.5
        time.sleep(0.05)
        return total

    result = dummy_workload()
    print(f"[ok] dummy decorated function returned: {result:.1f}")

    report_path = PROJECT_ROOT / "data" / "resource_usage.json"
    assert report_path.is_file(), f"resource usage report missing: {report_path}"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert "runtime_seconds" in report, "missing key runtime_seconds"
    assert "peak_ram_gb" in report, "missing key peak_ram_gb"
    print(f"[ok] resource usage report: {report}")
    return report


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    create_directories()
    verify_code_package_logger()
    run_dummy_decorated_function()
    print("T001 skeleton setup completed successfully.")


if __name__ == "__main__":
    main()
