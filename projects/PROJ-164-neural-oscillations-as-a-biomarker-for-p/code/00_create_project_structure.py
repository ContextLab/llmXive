"""T001a: Create the project directory tree (FR-001).

Creates the directories required by the project structure:
code/, code/utils/, tests/, data/raw, data/processed, data/synthetic,
models/, docs/, docs/contracts/, state/projects/

Writes evidence of the resulting tree to docs/structure_report.txt.
"""
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "tests",
    "data/raw",
    "data/processed",
    "data/synthetic",
    "models",
    "docs",
    "docs/contracts",
    "state/projects",
]


def create_structure(root: Path) -> list:
    """Create all required directories under root; return list of created dirs."""
    created = []
    for d in REQUIRED_DIRS:
        target = root / d
        target.mkdir(parents=True, exist_ok=True)
        if not target.is_dir():
            raise RuntimeError(f"Failed to create directory: {target}")
        created.append(target)
    return created


def write_report(root: Path, created: list) -> Path:
    """Write a directory-listing evidence report."""
    report_path = paths.docs("structure_report.txt")
    lines = [
        "T001a project structure creation report",
        "=" * 40,
        f"Project root: {root}",
        "",
        "Required directories and their existence:",
    ]
    ok = True
    for d in REQUIRED_DIRS:
        target = root / d
        exists = target.is_dir()
        ok = ok and exists
        lines.append(f"  {d:20s} exists={exists}")
    lines += [
        "",
        "Directory listing of project root:",
    ]
    for p in sorted(root.iterdir()):
        kind = "DIR " if p.is_dir() else "FILE"
        lines.append(f"  [{kind}] {p.name}")
    lines += [
        "",
        "Directory listing of code/:",
    ]
    cdir = root / "code"
    if cdir.is_dir():
        for p in sorted(cdir.iterdir()):
            kind = "DIR " if p.is_dir() else "FILE"
            lines.append(f"  [{kind}] {p.name}")
    lines += [
        "",
        f"ALL_REQUIRED_DIRS_PRESENT: {ok}",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    root = paths.root
    log.info("Creating project structure under %s", root)
    created = create_structure(root)
    log.info("Ensured %d directories exist", len(created))
    report = write_report(root, created)
    log.info("Structure report written to %s", report)
    # Final verification: fail loudly if anything is missing
    for d in REQUIRED_DIRS:
        if not (root / d).is_dir():
            raise RuntimeError(f"Verification failed: missing {d}")
    print(f"OK: {len(REQUIRED_DIRS)} required directories present under {root}")
    print(f"Evidence report: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())