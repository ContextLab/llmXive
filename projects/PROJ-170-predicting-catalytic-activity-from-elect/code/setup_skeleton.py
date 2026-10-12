from llmxive_toolkit import paths
import os

def main():
    """
    Repair project skeleton by creating required directories and package init files.
    Uses llmxive_toolkit.paths to ensure folders are created in the correct project locations.
    """
    # 1. Create required directories
    # paths.<folder>(...) automatically creates the folder it lives in
    required_dirs = [
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
    
    for d in required_dirs:
        # Explicitly call mkdir just to be absolutely certain and for logging
        d.mkdir(parents=True, exist_ok=True)
        print(f"Verified directory: {d}")

    # 2. Create empty __init__.py files for package structure
    init_files = [
        paths.code("__init__.py"),
        paths.code("utils/__init__.py"),
        paths.code("models/__init__.py"),
    ]
    
    for f in init_files:
        f.touch()
        print(f"Created init file: {f}")

if __name__ == "__main__":
    main()
