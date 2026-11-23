"""
T001: Create the project structure per the implementation plan.

Ensures the canonical source tree lives under ``code/src/`` (the location
used by every quickstart command, e.g. ``python code/src/data_synthesis/generator.py``)
and that the supporting ``tests/`` and ``data/`` directories exist.

Directories created (idempotent — existing files are never overwritten):
    code/src/data_synthesis/
    code/src/feature_extraction/
    code/src/baseline/
    code/src/scheduler/
    code/src/utils/
    tests/unit/ tests/integration/ tests/contract/
    data/raw/ data/features/ data/baseline/ data/processed/

Writes a verification report to ``results/structure_report.json``.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger("setup_structure")

PROJECT_ROOT = paths.root

SRC_PACKAGES = [
    "data_synthesis",
    "feature_extraction",
    "baseline",
    "scheduler",
    "utils",
]

TEST_DIRS = [
    ("tests",),
    ("tests", "unit"),
    ("tests", "integration"),
    ("tests", "contract"),
]

DATA_DIRS = [
    ("data", "raw"),
    ("data", "features"),
    ("data", "baseline"),
    ("data", "processed"),
]


def ensure_dir(path: Path) -> str:
    """Create directory if missing; return 'created' or 'exists'."""
    if path.exists() and path.is_dir():
        return "exists"
    path.mkdir(parents=True, exist_ok=True)
    return "created"


def ensure_package_init(package_dir: Path) -> str:
    """Ensure a Python package has an __init__.py; never overwrite."""
    init_path = package_dir / "__init__.py"
    if init_path.exists():
        return "exists"
    init_path.write_text(
        '"""Package initializer (auto-created by T001 setup_structure.py)."""\n',
        encoding="utf-8",
    )
    return "created"


def main() -> int:
    report = {
        "task_id": "T001",
        "project_root": str(PROJECT_ROOT),
        "source_packages": {},
        "test_directories": {},
        "data_directories": {},
        "errors": [],
    }

    # Source packages under code/src/
    src_root = PROJECT_ROOT / "code" / "src"
    report["source_packages"]["code/src"] = ensure_dir(src_root)
    for pkg in SRC_PACKAGES:
        pkg_dir = src_root / pkg
        try:
            dir_status = ensure_dir(pkg_dir)
            init_status = ensure_package_init(pkg_dir)
            report["source_packages"][f"code/src/{pkg}"] = {
                "directory": dir_status,
                "init_py": init_status,
            }
        except OSError as exc:
            report["errors"].append(f"code/src/{pkg}: {exc}")

    # Test directories
    for parts in TEST_DIRS:
        d = PROJECT_ROOT.joinpath(*parts)
        try:
            report["test_directories"]["/".join(parts)] = ensure_dir(d)
        except OSError as exc:
            report["errors"].append(f"{'/'.join(parts)}: {exc}")

    # Data directories
    for parts in DATA_DIRS:
        d = PROJECT_ROOT.joinpath(*parts)
        try:
            report["data_directories"]["/".join(parts)] = ensure_dir(d)
        except OSError as exc:
            report["errors"].append(f"{'/'.join(parts)}: {exc}")

    # Verification: every required path must now exist
    required = [src_root / p for p in SRC_PACKAGES]
    required += [PROJECT_ROOT.joinpath(*parts) for parts in TEST_DIRS]
    required += [PROJECT_ROOT.joinpath(*parts) for parts in DATA_DIRS]
    missing = [str(p.relative_to(PROJECT_ROOT)) for p in required if not p.is_dir()]

    report["all_required_paths_present"] = not missing and not report["errors"]
    report["missing_paths"] = missing

    out_path = paths.results("structure_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if report["all_required_paths_present"]:
        log.info("Project structure verified. Report: %s", out_path)
        print(f"Structure OK. Report written to {out_path}")
        return 0
    log.error("Structure incomplete: %s", missing or report["errors"])
    print(f"Structure INCOMPLETE: {missing or report['errors']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())