import os
import sys
from pathlib import Path


def create_init_files(root_dir: str = ".") -> None:
    """
    Create __init__.py files in all Python package directories.

    Args:
        root_dir: Root directory to scan for packages (default: current directory)
    """
    path = Path(root_dir)
    if not path.exists():
        raise FileNotFoundError(f"Directory {root_dir} does not exist")

    # Define package directories that need __init__.py
    package_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    created_count = 0
    for pkg_dir in package_dirs:
        full_path = path / pkg_dir
        if full_path.exists() and full_path.is_dir():
          init_file = full_path / "__init__.py"
          if not init_file.exists():
              # Create a basic docstring for the package
              init_file.write_text(
                  f'"""\n{pkg_dir.replace("/", ".")} package.\n"""\n'
              )
              print(f"Created: {init_file}")
              created_count += 1
          else:
              print(f"Exists:  {init_file}")
        else:
          print(f"Skipped (missing): {full_path}")

    print(f"\nTotal __init__.py files created/verified: {created_count}")


def main() -> None:
    """Main entry point for init file creation."""
    root = os.getenv("PROJECT_ROOT", ".")
    try:
        create_init_files(root)
    except Exception as e:
        print(f"Error creating init files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
