import subprocess
from pathlib import Path
import sys


def run_black_isort() -> bool:
    """
    Wrapper to run black and isort, ensuring they are installed.
    Returns True if successful, False otherwise.
    """
    repo_root = Path(__file__).parent.parent
    code_dir = repo_root / "code"
    tests_dir = repo_root / "tests"

    # Ensure dependencies are installed
    print("Checking/installing formatting dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "black", "isort"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("Failed to install black or isort.")
        return False

    print(f"Running isort on {code_dir} and {tests_dir}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "isort", str(code_dir), str(tests_dir)],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"isort failed: {e}")
        return False

    print(f"Running black on {code_dir} and {tests_dir}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "black", str(code_dir), str(tests_dir)],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"black failed: {e}")
        return False

    return True


def main():
    if run_black_isort():
        print("Formatting pipeline completed successfully.")
    else:
        print("Formatting pipeline failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
