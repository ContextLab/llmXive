"""Project scaffolding for the VAERS disproportionality analysis (T001).

Creates the required directory tree and writes a three-level filesystem
snapshot to ``logs/structure.txt`` using ``tree -a -L 3`` when available,
falling back to ``find . -maxdepth 3 -type d`` (and finally to a pure
Python walk) so the verification ``test -s logs/structure.txt`` always
succeeds on a real filesystem.
"""

import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_DIRS = [
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "data/raw",
    "data/processed",
    "data/results",
    "output/figures",
    "output/temporal_profiles",
    "logs",
]


def create_directories() -> None:
    """Create all required project directories (idempotent)."""
    root = paths.root
    for dir_path in REQUIRED_DIRS:
        (root / dir_path).mkdir(parents=True, exist_ok=True)
        log.info("Ensured directory: %s", dir_path)


def _python_tree_fallback(max_depth: int = 3) -> str:
    """Pure-Python replacement for ``tree -a -L 3``."""
    root = paths.root
    lines = ["."]
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if len(rel.parts) > max_depth:
            continue
        lines.append(str(rel))
    return "\n".join(lines) + "\n"


def write_structure_snapshot() -> None:
    """Capture a three-level directory listing into logs/structure.txt."""
    output_file = paths.logs("structure.txt")
    log.info("Writing structure snapshot to %s", output_file)

    output = None
    try:
        result = subprocess.run(
            ["tree", "-a", "-L", "3"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(paths.root),
        )
        output = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        log.info("tree unavailable, falling back to find")
        try:
            result = subprocess.run(
                ["find", ".", "-maxdepth", "3", "-type", "d"],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(paths.root),
            )
            output = result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            log.info("find unavailable, falling back to pure-Python walk")
            output = _python_tree_fallback()

    output_file.write_text(output, encoding="utf-8")

    if not output_file.is_file() or output_file.stat().st_size == 0:
        raise RuntimeError("structure.txt was not written or is empty")

    listed = sum(
        1
        for d in REQUIRED_DIRS
        if d in output or ("./" + d) in output or str(Path(d)) in output
    )
    log.info(
        "Structure snapshot written (%d bytes, %d/%d required dirs listed)",
        output_file.stat().st_size,
        listed,
        len(REQUIRED_DIRS),
    )
    if listed == 0:
        raise RuntimeError(
            "structure.txt does not mention any required directory"
        )


def main() -> None:
    """Main entry point for project scaffolding."""
    create_directories()
    write_structure_snapshot()
    log.info("Project structure established and snapshot recorded.")


if __name__ == "__main__":
    main()
