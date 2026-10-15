"""T001a: Create the project directory structure.

Creates the required directories at the project root:
  - src/ (with ingestion, modeling, analysis, utils, cli, research subpackages)
  - tests/ (with contract, unit, integration subdirectories)
  - specs/001-predicting-reaction-mechanisms-from-spec/
  - data/ (with raw, processed, reference, results subdirectories)
  - state/projects/

Each directory is seeded with a .gitkeep file so it is non-empty and
survives version control. A full recursive directory listing is written
to specs/001-predicting-reaction-mechanisms-from-spec/directory_structure.txt as
evidence that the structure exists and is non-empty.
"""

from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

ROOT = paths.root

DIRECTORIES = [
    "src",
    "src/ingestion",
    "src/modeling",
    "src/analysis",
    "src/utils",
    "src/cli",
    "src/research",
    "tests",
    "tests/contract",
    "tests/unit",
    "tests/integration",
    "specs/001-predicting-reaction-mechanisms",
    "specs/001-predicting-reaction-mechanisms-from-spec/contracts",
    "data",
    "data/raw",
    "data/raw/nist",
    "data/raw/pubchem",
    "data/processed",
    "data/reference",
    "data/results",
    "state",
    "state/projects",
]

EVIDENCE_FILE = (
    "specs/001-predicting-reaction-mechanisms-from-spec/directory_structure.txt"
)


def create_directories(root: Path = ROOT) -> list:
    """Create every required directory and seed it with .gitkeep.

    Returns the list of created directory paths (as strings).
    """
    created = []
    for rel in DIRECTORIES:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        created.append(str(d))
        log.info("Ensured directory: %s", d)
    return created


def write_evidence(root: Path = ROOT) -> Path:
    """Write a recursive listing of the created structure as evidence."""
    lines = [
        "T001a directory structure evidence",
        f"Project root: {root}",
        "",
    ]
    for rel in DIRECTORIES:
        d = root / rel
        if not d.is_dir():
            raise RuntimeError(f"Expected directory missing: {d}")
        entries = sorted(p.name for p in d.iterdir())
        lines.append(f"{rel}/  ({len(entries)} entries: {entries})")
    lines.append("")
    lines.append("Full recursive listing of created directories:")
    for rel in DIRECTORIES:
        d = root / rel
        for p in sorted(d.rglob("*")):
            kind = "DIR " if p.is_dir() else "FILE"
            lines.append(f"[{kind}] {p.relative_to(root)}")
    out_path = root / EVIDENCE_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Wrote directory structure evidence to %s", out_path)
    return out_path


def main() -> None:
    created = create_directories()
    evidence = write_evidence()
    missing = [c for c in created if not Path(c).is_dir()]
    if missing:
        raise RuntimeError(f"Directories missing after creation: {missing}")
    print(f"Created/verified {len(created)} directories.")
    print(f"Evidence listing written to: {evidence}")


if __name__ == "__main__":
    main()