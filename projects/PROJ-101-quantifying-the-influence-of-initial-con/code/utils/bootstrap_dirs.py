"""
T001: Create the required top-level directory layout and record it.

Creates the nine required directories under the project root and writes
a directory-structure listing (``dir_structure.txt``) that contains all
nine directory names so CI can verify the layout.

NOTE: the original task placed the listing under ``state/``, but that
path is owned by the platform. The listing is therefore recorded under
the project-owned ``data/processed/`` directory instead.
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

# 'state/' is platform-owned; the recorded layout lives in data/processed.
STATE_SUBSTITUTE_DIR = "data/processed"
OUTPUT_FILE = "dir_structure.txt"


def build_tree(root: Path, depth: int = 2) -> str:
    """Build a ``tree -L depth``-style listing of the directory layout."""
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
        _walk(root, entry, depth - 1, prefix + ("    " if last else "│   "), lines)


def main() -> Path:
    root = paths.root

    # 1. Create every required directory (plus the substitute for state/).
    created = []
    for rel in REQUIRED_DIRS + [STATE_SUBSTITUTE_DIR]:
        d = root / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)

    # 2. Build the tree listing and write it to the project-owned location.
    tree_text = build_tree(root, depth=2)
    out_path = paths.data("processed", OUTPUT_FILE)
    out_path.write_text(tree_text, encoding="utf-8")

    # 3. Verify that all nine required directories are recorded.
    content = out_path.read_text(encoding="utf-8")
    missing = [rel for rel in REQUIRED_DIRS if rel.split("/")[-1] not in content]
    if missing:
        raise RuntimeError(
            f"dir_structure.txt is missing required directories: {missing}"
        )

    print(f"Created directories: {created or '(all already present)'}")
    print(f"Directory structure recorded in {out_path}")
    return out_path


if __name__ == "__main__":
    main()