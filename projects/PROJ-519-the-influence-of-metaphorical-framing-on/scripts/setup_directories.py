"""T001a: Create the src/ and tests/ directories at the repository root.

This script ensures both directories exist and contain placeholder files
(__init__.py / .gitkeep) so the structure is committed to version control
and visible on the filesystem.
"""
from pathlib import Path

from llmxive_toolkit import paths

def ensure_dir(rel: str, placeholder: str) -> Path:
    directory = paths.path(rel)
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / placeholder
    if not marker.exists():
        marker.write_text("", encoding="utf-8")
    return directory

def main() -> None:
    src_dir = ensure_dir("src", "__init__.py")
    tests_dir = ensure_dir("tests", "__init__.py")
    # .gitkeep markers so empty dirs survive git
    for d in (src_dir, tests_dir):
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
    print(f"Created/verified: {src_dir}")
    print(f"Created/verified: {tests_dir}")

if __name__ == "__main__":
    main()