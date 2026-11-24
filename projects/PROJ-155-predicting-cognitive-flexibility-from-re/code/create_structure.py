"""
Create the required project directory skeleton.
"""
from pathlib import Path

from llmxive_toolkit import paths


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def main():
    # Directories explicitly required by T001
    dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
        paths.figures(),
        paths.docs(),
        paths.tests(),
        paths.data("logs"), # Needed for linting output
    ]
    for d in dirs:
        ensure_dir(d)
    print("Project skeleton created successfully.")

if __name__ == "__main__":
    main()
