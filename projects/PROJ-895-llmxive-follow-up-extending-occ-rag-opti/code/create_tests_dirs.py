"""Create the tests directory structure for the OCC-RAG sparse-core project.

Creates tests/, tests/contract/, tests/integration/, and tests/unit/
(with .gitkeep placeholders so the empty directories persist in git).
"""
from llmxive_toolkit import paths

SUBDIRS = ["contract", "integration", "unit"]


def main() -> None:
    for sub in SUBDIRS:
        d = paths.path("tests", sub)
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.touch()
        print(f"OK {d}")
    print("Tests directory structure created successfully.")


if __name__ == "__main__":
    main()