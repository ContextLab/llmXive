"""
Test that core project directories are tracked by git via .gitkeep files.
"""
import subprocess
import sys

def get_git_tracked_files():
    """Return a set of file paths tracked by git."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        files = result.stdout.strip().splitlines()
        return set(files)
    except subprocess.CalledProcessError as e:
        # If git command fails, abort the test with a clear message.
        raise RuntimeError(f"git ls-files failed: {e.stderr}") from e

def test_core_directories_tracked():
    """Ensure each core directory contains a .gitkeep file tracked by git."""
    tracked_files = get_git_tracked_files()

    required_gitkeep_paths = {
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/assets/.gitkeep",
        "code/.gitkeep",
        "artifacts/.gitkeep",
        "tests/.gitkeep",
    }

    missing = required_gitkeep_paths - tracked_files
    assert not missing, f"The following .gitkeep files are missing from git tracking: {sorted(missing)}"

if __name__ == "__main__":
    # Allow running the test directly for quick debugging.
    try:
        test_core_directories_tracked()
        print("All core .gitkeep files are tracked by git.")
    except AssertionError as err:
        print(f"TEST FAILED: {err}", file=sys.stderr)
        sys.exit(1)