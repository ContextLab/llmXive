"""
Script to verify and initialize linting and formatting tools.
This script ensures that 'ruff' and 'black' are installed and
provides commands to run them.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Execute a command and report success/failure."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found. Please install the tool: {' '.join(cmd[:1])}")
        return False

def main():
    """Main entry point for setup_linting."""
    print("=" * 60)
    print("LLM-Xive Project Linting & Formatting Setup")
    print("=" * 60)

    # 1. Verify installations
    print("\n[Step 1] Checking tool availability...")
    tools_ok = True
    
    # Check Ruff
    if not run_command([sys.executable, "-m", "ruff", "--version"], "Ruff version check"):
        tools_ok = False
    
    # Check Black
    if not run_command([sys.executable, "-m", "black", "--version"], "Black version check"):
        tools_ok = False

    if not tools_ok:
        print("\n⚠️  Tools are missing. Please install dependencies:")
        print(f"   {sys.executable} -m pip install -r requirements.txt")
        sys.exit(1)

    # 2. Run Linting (Check only)
    print("[Step 2] Running Ruff check (linting)...")
    # We run check --fix to auto-fix simple issues, but we don't fail if fixes are needed
    # unless we want to enforce strict CI. For setup, we just show the report.
    run_command(
        [sys.executable, "-m", "ruff", "check", "."],
        "Ruff linting check"
    )

    # 3. Run Formatting (Check only)
    print("[Step 3] Running Black check (formatting)...")
    # --check returns 1 if files need reformatting
    if not run_command(
        [sys.executable, "-m", "black", "--check", "."],
        "Black formatting check"
    ):
        print("ℹ️  Some files need formatting. Run: black . to fix.")

    # 4. Suggest fix commands
    print("\n" + "=" * 60)
    print("Setup Complete.")
    print("To auto-fix linting issues and format code, run:")
    print(f"   {sys.executable} -m ruff check . --fix")
    print(f"   {sys.executable} -m black .")
    print("=" * 60)

if __name__ == "__main__":
    main()
