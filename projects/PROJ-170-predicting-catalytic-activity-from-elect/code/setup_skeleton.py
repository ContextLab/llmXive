from llmxive_toolkit import paths
from pathlib import Path

def main():
    """
    Repair project skeleton by creating required directories and package initialization files.
    """
    # Directories to create
    dir_paths = [
        paths.data("raw"),
        paths.data("processed"),
        paths.path("outputs"),
        paths.code(),
        paths.code("utils"),
        paths.code("models"),
        paths.path("tests/contract"),
        paths.path("tests/integration"),
        paths.path("tests/unit"),
    ]

    for p in dir_paths:
        p.mkdir(parents=True, exist_ok=True)

    # Package initialization files to create
    init_files = [
        paths.code("__init__.py"),
        paths.code("utils/__init__.py"),
        paths.code("models/__init__.py"),
    ]

    for f in init_files:
        f.touch()

if __name__ == "__main__":
    main()
