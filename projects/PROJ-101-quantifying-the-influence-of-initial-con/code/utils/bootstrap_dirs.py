"""
T001: Create the required top‑level directory layout and record it.

This script creates the nine required project directories (excluding the
platform‑owned ``state/`` directory) and writes a ``tree -L 2``‑style
listing of the layout to ``data/processed/dir_structure.txt``.  The
listing is later used by CI to verify that the expected directories
exist.
"""

from pathlib import Path

from llmxive_toolkit import paths

# The nine required directories (relative to the project root).
REQUIRED_DIRS = [
    "code",
    "code/simulation",
    "code/analysis",
    "code/utils",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
]

# Output file (project‑owned location).
OUTPUT_FILE = "dir_structure.txt"


def build_tree(root: Path, depth: int = 2) -> str:
    """Build a ``tree -L depth``‑style listing of the directory layout."""
    lines = [f"{root.name}/"]
    _walk(root, root, depth, prefix="", lines=lines)
    return "\n".join(lines) + "\n"


def _walk(root: Path, current: Path, depth: int, prefix: str, lines: list) -> None:
    if depth <= 0:
        return
    try:
        entries = sorted(
            [p for p in current.iterdir() if p.is_dir()],
            key=lambda p: p.name,
        )
    except OSError:
        return
    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        connector = "└── " if last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}/")
        _walk(
            root,
            entry,
            depth - 1,
            prefix + ("    " if last else "│   "),
            lines,
        )


def main() -> Path:
    """Create directories and write the directory‑structure listing."""
    root = paths.root

    # 1. Create each required directory (parents=True ensures the full
    #    hierarchy is built).
    for rel in REQUIRED_DIRS:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)

    # 2. Build the tree representation and write it to the project‑owned
    #    location.
    tree_text = build_tree(root, depth=2)
    out_path = paths.data("processed", OUTPUT_FILE)
    out_path.write_text(tree_text, encoding="utf-8")

    # 3. Simple sanity check – ensure every required directory name appears
    #    in the recorded text.
    missing = [
        rel for rel in REQUIRED_DIRS if rel.split("/")[-1] not in tree_text
    ]
    if missing:
        raise RuntimeError(
            f"dir_structure.txt is missing required directories: {missing}"
        )

    print(f"Created directories (if needed): {REQUIRED_DIRS}")
    print(f"Directory structure recorded in {out_path}")
    return out_path


if __name__ == "__main__":
    main()