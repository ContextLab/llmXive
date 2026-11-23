"""
Script to verify and document the linting/formatting configuration.
This script checks if ruff and black are installed and validates the config files.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed in the current environment."""
    success, output = run_command([sys.executable, "-m", "pip", "show", tool_name])
    return success and "Name:" in output

def main():
    print("Verifying Linting and Formatting Configuration for PROJ-754...")
    print("-" * 60)

    # Check for black
    if check_tool_installed("black"):
        print("[OK] Black is installed.")
        success, output = run_command(["black", "--version"])
        if success:
            print(f"    {output.strip()}")
        else:
            print(f"    [WARN] Could not verify black version: {output}")
    else:
        print("[WARN] Black is NOT installed. Install with: pip install black")

    # Check for ruff
    if check_tool_installed("ruff"):
        print("[OK] Ruff is installed.")
        success, output = run_command(["ruff", "--version"])
        if success:
            print(f"    {output.strip()}")
        else:
            print(f"    [WARN] Could not verify ruff version: {output}")
    else:
        print("[WARN] Ruff is NOT installed. Install with: pip install ruff")

    # Check config files exist
    root = Path(__file__).resolve().parent.parent.parent
    config_files = {
        "pyproject.toml": root / "pyproject.toml",
        ".pre-commit-config.yaml": root / ".pre-commit-config.yaml",
    }

    print("-" * 60)
    print("Configuration Files Status:")
    all_present = True
    for name, path in config_files.items():
        if path.exists():
            print(f"[OK] {name} exists at {path}")
        else:
            print(f"[MISSING] {name} not found at {path}")
            all_present = False

    if all_present:
        print("-" * 60)
        print("Configuration validation complete. Ready to run:")
        print("  pre-commit install")
        print("  pre-commit run --all-files")
        print("  ruff check .")
        print("  black . --check")
    else:
        print("[FAIL] Missing configuration files.")
        sys.exit(1)

if __name__ == "__main__":
    main()