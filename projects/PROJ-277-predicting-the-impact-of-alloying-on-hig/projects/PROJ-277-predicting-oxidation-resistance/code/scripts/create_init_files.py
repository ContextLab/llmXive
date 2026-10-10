"""Create empty __init__.py files for all Python packages in the project.

Task T001b: ensures every Python package directory under
projects/PROJ-277-predicting-oxidation-resistance/ contains an
(empty) __init__.py so the directories are importable packages.
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

PACKAGE_DIRS = [
    "code",
    "code/data",
    "code/models",
    "code/viz",
    "code/utils",
    "code/scripts",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]


def create_init_files(project_root: str = PROJECT_ROOT) -> list:
    """Create empty __init__.py in each package dir; return created paths."""
    created = []
    for rel in PACKAGE_DIRS:
        pkg_dir = os.path.join(project_root, rel)
        os.makedirs(pkg_dir, exist_ok=True)
        init_path = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w", encoding="utf-8"):
                pass
            created.append(init_path)
    return created


def main():
    created = create_init_files()
    if created:
        for path in created:
            print(f"created: {path}")
    else:
        print("all __init__.py files already present")
    # Verify all required files exist
    missing = [
        rel
        for rel in PACKAGE_DIRS
        if not os.path.exists(
            os.path.join(PROJECT_ROOT, rel, "__init__.py")
        )
    ]
    if missing:
        print(f"ERROR: missing __init__.py in: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {len(PACKAGE_DIRS)} packages verified")


if __name__ == "__main__":
    main()