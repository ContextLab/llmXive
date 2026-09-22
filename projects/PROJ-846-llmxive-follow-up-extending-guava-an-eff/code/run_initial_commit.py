"""
Task T001d: Run `git commit -m "Initial commit"` to create the initial commit.

This script executes the git commit command to finalize the initial repository state.
It relies on the repository being initialized (T001b) and files being staged (T001c).
"""
import subprocess
import sys
from pathlib import Path
from git_operations import run_git_command

def main():
    """Execute the initial git commit."""
    repo_root = Path(__file__).parent.parent
    print(f"Executing initial commit in: {repo_root}")

    try:
        # Run the commit command
        result = run_git_command(
            ["commit", "-m", "Initial commit"],
            cwd=repo_root
        )

        if result.returncode == 0:
            print("✅ Initial commit successful.")
            print(f"Output:\n{result.stdout}")
            if result.stderr:
                print(f"Stderr:\n{result.stderr}")
            return 0
        else:
            print(f"❌ Git commit failed with code {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            return 1

    except Exception as e:
        print(f"❌ Error executing git commit: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())