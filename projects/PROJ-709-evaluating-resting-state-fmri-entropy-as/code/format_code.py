import subprocess
import sys
from pathlib import Path


def run_formatter() -> bool:
    """
    Runs black and isort on the code/ and tests/ directories.
    Returns True if successful, False otherwise.
    """
    repo_root = Path(__file__).parent.parent
    code_dir = repo_root / "code"
    tests_dir = repo_root / "tests"

    print("Running isort on code/ and tests/...")
    try:
        subprocess.run(
            [sys.executable, "-m", "isort", str(code_dir), str(tests_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("isort completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running isort: {e}")
        return False

    print("Running black on code/ and tests/...")
    try:
        subprocess.run(
            [sys.executable, "-m", "black", str(code_dir), str(tests_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("black completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running black: {e}")
        return False

    return True


def main():
    success = run_formatter()
    if success:
        print("Code formatting completed successfully.")
    else:
        print("Code formatting failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
