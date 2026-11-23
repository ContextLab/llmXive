import os
import sys
import subprocess
from pathlib import Path

def ensure_directory_exists(path: str) -> None:
    """Ensure the given directory path exists."""
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True)
        print(f"Created directory: {dir_path}")

def write_config_file(filename: str, content: str) -> None:
    """Write content to a configuration file."""
    path = Path(filename)
    path.write_text(content)
    print(f"Written config file: {filename}")

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and print the result."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def main() -> None:
    """Main entry point to configure linting and formatting tools."""
    print("Configuring Ruff and Black for the project...")

    # Ensure project root is set correctly
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # 1. Install dependencies if not already present
    # The pyproject.toml already lists ruff and black, but we ensure they are available
    print("\n--- Checking/Installing dependencies ---")
    run_command(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        "Installing project dependencies (including ruff and black)"
    )

    # 2. Verify ruff is available
    print("\n--- Verifying Ruff ---")
    if not run_command([sys.executable, "-m", "ruff", "--version"], "Check Ruff version"):
        print("Warning: Ruff installation might have failed.")

    # 3. Verify black is available
    print("\n--- Verifying Black ---")
    if not run_command([sys.executable, "-m", "black", "--version"], "Check Black version"):
        print("Warning: Black installation might have failed.")

    # 4. Run initial check (linting)
    print("\n--- Running Ruff Check ---")
    # We ignore errors here as the codebase might not be perfect yet,
    # but we want to see the current state.
    run_command(
        [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
        "Running Ruff check on code and tests"
    )

    # 5. Run format check (dry run)
    print("\n--- Running Black Check (Dry Run) ---")
    run_command(
        [sys.executable, "-m", "black", "--check", "code/", "tests/"],
        "Running Black check on code and tests"
    )

    print("\n--- Configuration Complete ---")
    print("To fix linting errors: python -m ruff check --fix code/ tests/")
    print("To format code: python -m black code/ tests/")

if __name__ == "__main__":
    main()