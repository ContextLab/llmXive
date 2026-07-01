"""
Script to automatically format code using Black and sort imports using Ruff.
Usage: python code/format.py
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=False,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode == 0:
            print(f"✓ {description} completed successfully.\n")
        else:
            print(f"⚠ {description} completed with warnings or changes.\n")
        return True
    except FileNotFoundError:
        print(f"✗ Error: Command not found. Please ensure {command[0]} is installed.\n")
        print("Run: pip install -r code/requirements-dev.txt")
        return False

def main():
    """Main entry point for formatting script."""
    print("=" * 50)
    print("LLMXive Auto-Formatter")
    print("=" * 50 + "\n")

    target_dir = "code"

    # 1. Sort imports with Ruff
    ruff_cmd = ["ruff", "check", "--select", "I", "--fix", target_dir]
    run_command(ruff_cmd, "Ruff Import Sorting")

    # 2. Format code with Black
    black_cmd = ["black", target_dir]
    run_command(black_cmd, "Black Code Formatting")

    print("Formatting complete.")

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
