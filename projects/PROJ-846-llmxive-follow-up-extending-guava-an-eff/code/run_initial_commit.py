import subprocess
import sys
from pathlib import Path
from code.git_operations import run_git_command
from code.init_git_repo import initialize_git_repository

def main():
    project_root = Path(__file__).resolve().parent.parent
    print("Running initial commit process...")
    success = initialize_git_repository(project_root)
    if success:
        # Verify commit exists
        stdout, stderr, code = run_git_command(["log", "-1"], cwd=project_root)
        if code == 0:
            print("Verification: Commit history contains at least one entry.")
            return 0
        else:
            print("Verification failed: Could not read commit history.")
            return 1
    else:
        print("Initialization failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())