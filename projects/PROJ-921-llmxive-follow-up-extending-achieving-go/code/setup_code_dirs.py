"""Create the code/ directory structure for the llmXive follow-up project.

Task T001a: ensures the directories code/data, code/inference,
code/scoring, code/analysis, and code/utils exist, each containing a
.gitkeep placeholder so the empty directories are tracked by git.
Running this script prints a listing of the created structure as
evidence.
"""
from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_SUBDIRS = ["data", "inference", "scoring", "analysis", "utils"]


def setup_code_directories() -> list[Path]:
    """Create code/ and its required subdirectories.

    Returns the list of created/verified directory paths.
    """
    code_root = paths.code()
    created = []
    for sub in REQUIRED_SUBDIRS:
        d = code_root / sub
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        created.append(d)
    return created


def main() -> None:
    dirs = setup_code_directories()
    print("code/ directory structure created:")
    for d in dirs:
        print(f"  {d}  (exists={d.is_dir()})")
    code_root = paths.code()
    print("\nFull listing of code/:")
    for p in sorted(code_root.rglob("*")):
        print(f"  {p.relative_to(code_root.parent)}")


if __name__ == "__main__":
    main()