#!/usr/bin/env python3
"""T001: Create the project structure per the implementation plan.

Ensures the directories required by plan.md exist and are populated:
    code/src/, code/scripts/, code/tests/

For each directory, this script:
  1. Creates the directory if missing (including parents).
  2. Ensures a package marker (__init__.py) exists for src/ and tests/.
  3. Records a full directory listing as evidence in
     artifacts/project_structure.txt so the structure can be verified.

Run:
    python code/scripts/setup_project_structure.py
"""
import sys
from pathlib import Path

# Project root = repository root (two levels above this file).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"

REQUIRED_DIRS = [
    CODE_DIR / "src",
    CODE_DIR / "scripts",
    CODE_DIR / "tests",
]

# Directories that must contain at least one file to count as populated.
PACKAGE_MARKERS = {
    CODE_DIR / "src": "__init__.py",
    CODE_DIR / "tests": "__init__.py",
}

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORT_PATH = ARTIFACTS_DIR / "project_structure.txt"


def create_structure() -> dict:
    """Create required directories and package markers.

    Returns:
        dict summarizing created directories, created markers, and
        file counts per directory.
    """
    summary = {"created_dirs": [], "created_markers": [], "file_counts": {}}

    for d in REQUIRED_DIRS:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            summary["created_dirs"].append(str(d.relative_to(PROJECT_ROOT)))

    for d, marker in PACKAGE_MARKERS.items():
        marker_path = d / marker
        if not marker_path.exists():
            marker_path.write_text(
                '# Package marker for the significance-reliability pipeline.\n',
                encoding="utf-8",
            )
            summary["created_markers"].append(
                str(marker_path.relative_to(PROJECT_ROOT))
            )

    for d in REQUIRED_DIRS:
        files = sorted(p for p in d.rglob("*") if p.is_file())
        summary["file_counts"][str(d.relative_to(PROJECT_ROOT))] = len(files)

    return summary


def write_report(summary: dict) -> Path:
    """Write a directory-listing report as verifiable evidence."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "Project structure report (T001)",
        "================================",
        "",
        "Required directories:",
    ]
    for d in REQUIRED_DIRS:
        rel = d.relative_to(PROJECT_ROOT)
        status = "CREATED" if str(rel) in summary["created_dirs"] else "exists"
        lines.append(f"  {rel} [{status}] - {summary['file_counts'][str(rel)]} files")

    if summary["created_markers"]:
        lines.append("")
        lines.append("Package markers created:")
        lines.extend(f"  {m}" for m in summary["created_markers"])

    lines.append("")
    lines.append("Directory listings:")
    for d in REQUIRED_DIRS:
        rel = d.relative_to(PROJECT_ROOT)
        lines.append(f"  {rel}/")
        for p in sorted(d.rglob("*")):
            if p.is_file():
                lines.append(f"    {p.relative_to(PROJECT_ROOT)}")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def main() -> int:
    summary = create_structure()

    missing = [
        str(d.relative_to(PROJECT_ROOT))
        for d in REQUIRED_DIRS
        if not d.is_dir()
    ]
    if missing:
        print(f"FAILED to create: {missing}", file=sys.stderr)
        return 1

    report = write_report(summary)
    print("Project structure verified:")
    for d in REQUIRED_DIRS:
        rel = d.relative_to(PROJECT_ROOT)
        print(
            f"  {rel}/ - {summary['file_counts'][str(rel)]} files "
            f"({'created' if str(rel) in summary['created_dirs'] else 'pre-existing'})"
        )
    print(f"Structure report written to: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())