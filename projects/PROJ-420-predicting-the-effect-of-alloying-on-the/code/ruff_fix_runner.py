"""
T035: Run `ruff==0.1.6 check --fix code/` (config: `pyproject.toml`).

This script executes the ruff linter with auto-fix enabled on the `code/` directory.
It ensures the project's Python code adheres to the formatting rules defined in pyproject.toml.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run ruff check --fix on the code directory."""
    project_root = Path(__file__).resolve().parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"Error: Directory {code_dir} does not exist.", file=sys.stderr)
        sys.exit(1)

    # Construct the ruff command
    # We explicitly invoke the module to ensure the correct version is used if installed in venv,
    # or fall back to the system ruff if the version in requirements.txt is installed globally.
    # The requirement is ruff==0.1.6.
    cmd = [
        sys.executable, "-m", "ruff", 
        "check", 
        "--fix", 
        str(code_dir)
    ]

    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False,  # Stream output to the runner
            text=True
        )
        
        if result.returncode != 0:
            # Ruff returns non-zero if errors remain that couldn't be fixed
            print("\nRuff check completed with fixes, but some issues may remain.", file=sys.stderr)
            # We do not exit with error code here unless the task strictly requires 100% clean code.
            # However, typically "check --fix" implies we want it to pass. 
            # If the task is just to "run" it, we report the status.
            # Given the context of fixing the project to pass execution, we assume we want it clean.
            # But ruff might find issues we can't fix automatically.
            # Let's exit with the return code so the pipeline knows if it's clean.
            sys.exit(result.returncode)
        
        print("Ruff check --fix completed successfully.")
        sys.exit(0)

    except FileNotFoundError:
        print("Error: 'ruff' command not found. Please install ruff==0.1.6.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running ruff: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()