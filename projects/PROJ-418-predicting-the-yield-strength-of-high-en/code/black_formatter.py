import os
import sys
import subprocess
from pathlib import Path


def format_with_black(root_dir: str = ".") -> None:
    """
    Run black formatter on the specified directory.

    Args:
        root_dir: Root directory to format (default: current directory)
    """
    path = Path(root_dir)
    if not path.exists():
        raise FileNotFoundError(f"Directory {root_dir} does not exist")

    print(f"Running black formatter on {path.absolute()}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "black", str(path)],
            check=True,
            capture_output=False,
        )
        print("Black formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Black formatting failed: {e}")
        raise


def main() -> None:
    """Main entry point for black formatting."""
    root = os.getenv("PROJECT_ROOT", ".")
    try:
        format_with_black(root)
    except Exception as e:
        print(f"Error during formatting: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
