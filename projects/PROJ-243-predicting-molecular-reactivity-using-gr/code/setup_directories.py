"""T001: Create core project directories with .gitkeep files.

Creates data/raw, data/processed, data/assets, code, artifacts, tests
(each with a .gitkeep placeholder so the empty directories are tracked
by git), and prints a listing proving their existence.
"""
import os
import sys

DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/assets",
    "code",
    "artifacts",
    "tests",
]


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    created = []
    for rel in DIRECTORIES:
        d = os.path.join(root, rel)
        os.makedirs(d, exist_ok=True)
        keep = os.path.join(d, ".gitkeep")
        if not os.path.exists(keep):
            with open(keep, "w", encoding="utf-8") as f:
                f.write("")
        created.append(rel)

    # Verification: list every directory and its .gitkeep
    ok = True
    print("Directory verification:")
    for rel in DIRECTORIES:
        d = os.path.join(root, rel)
        keep = os.path.join(d, ".gitkeep")
        exists = os.path.isdir(d) and os.path.isfile(keep)
        ok = ok and exists
        print(f"  {rel}: dir={os.path.isdir(d)} gitkeep={os.path.isfile(keep)}")

    if not ok:
        print("ERROR: some directories or .gitkeep files are missing.",
              file=sys.stderr)
        return 1
    print(f"Created/verified {len(created)} directories with .gitkeep files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())