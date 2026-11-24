"""Create the project directory structure for PROJ-848.

Task T001a: ensure the directories
{code, data, specs, state} exist (plus the standard subdirectories
used by later tasks) and leave a marker file in each so the tree is
preserved by version control and verifiable on disk.
"""
import os
import sys


def main():
    # The project root is the directory containing this script's parent.
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Project root: {root}")

    directories = [
        os.path.join(root, "code"),
        os.path.join(root, "code", "src"),
        os.path.join(root, "code", "tests"),
        os.path.join(root, "code", "tests", "integration"),
        os.path.join(root, "data"),
        os.path.join(root, "data", "raw"),
        os.path.join(root, "data", "processed"),
        os.path.join(root, "data", "results"),
        os.path.join(root, "specs"),
        os.path.join(root, "specs", "001-llmxive-motion-scaling"),
        os.path.join(root, "state"),
        os.path.join(root, "state", "projects"),
    ]

    for d in directories:
        os.makedirs(d, exist_ok=True)
        marker = os.path.join(d, ".gitkeep")
        if not os.path.exists(marker):
            with open(marker, "w", encoding="utf-8") as fh:
                fh.write("")
        print(f"OK  {os.path.relpath(d, root)}")

    print("Directory structure created successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())