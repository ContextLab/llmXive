"""T001: Create the project directory structure `code/` and `tests/`.

Ensures both directories exist, places a `.gitkeep` marker in `tests/`
if it is empty, and writes a directory listing as evidence to
`data/logs/structure_T001.txt`.
"""
from pathlib import Path

from llmxive_toolkit import paths

def main() -> None:
    root = paths.root
    code_dir = root / "code"
    tests_dir = root / "tests"

    code_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Keep the tests/ directory non-empty in version control if it has
    # no files yet (code/ already contains project modules).
    gitkeep = tests_dir / ".gitkeep"
    if not gitkeep.exists() and not any(tests_dir.iterdir()):
        gitkeep.write_text("", encoding="utf-8")

    lines = ["T001 directory structure evidence", ""]
    for d in (code_dir, tests_dir):
        lines.append(f"{d.relative_to(root)}/  (exists={d.is_dir()})")
        for entry in sorted(d.iterdir()):
            kind = "dir" if entry.is_dir() else "file"
            lines.append(f"  [{kind}] {entry.name}")
        lines.append("")

    out = paths.data("logs", "structure_T001.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote structure listing to {out}")
    print("\n".join(lines))

if __name__ == "__main__":
    main()