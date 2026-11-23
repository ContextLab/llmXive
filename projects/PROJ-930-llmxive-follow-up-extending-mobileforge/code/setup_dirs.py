"""Bootstrap script for T001: create the full directory tree.

Creates (with ``.gitkeep`` markers so empty directories survive in git):
    code/data/raw
    code/data/processed
    code/data/evaluation
    code/models
    code/utils
    code/tests/unit
    code/tests/integration

Note: ``state/`` is owned by the llmXive platform (it derives artifact
hashes at verification time), so this script deliberately does NOT
create or write into a project-local ``state/`` directory.
"""

from llmxive_toolkit import paths

DIRECTORIES = [
    ("data", "raw"),
    ("data", "processed"),
    ("data", "evaluation"),
    ("models",),
    ("utils",),
    ("tests", "unit"),
    ("tests", "integration"),
]


def main() -> None:
    created = []
    for parts in DIRECTORIES:
        # paths.code(...) returns <project>/code/<parts...> and creates
        # the directory (and any missing parents).
        target = paths.code(*parts)
        keep = target / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        created.append(str(target))
        print(f"[ok] {target}")

    print(f"\nCreated/verified {len(created)} directories under code/:")
    for c in created:
        print(f"  {c}")


if __name__ == "__main__":
    main()
