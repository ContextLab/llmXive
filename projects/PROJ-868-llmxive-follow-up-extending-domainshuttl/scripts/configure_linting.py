"""
Script to verify and validate linting and formatting configuration.
This script ensures that ruff, black, and flake8 are configured correctly
and can be executed against the project codebase.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report status."""
    print(f"Checking: {description}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"  ✓ {description} passed")
            return True
        else:
            print(f"  ✗ {description} failed:")
            print(f"    stdout: {result.stdout[:200]}")
            print(f"    stderr: {result.stderr[:200]}")
            return False
    except FileNotFoundError:
        print(f"  ✗ {description} failed: Command not found. Install with 'pip install {cmd[0]}'")
        return False


def main() -> int:
    """Main entry point for configuration verification."""
    print("Verifying Linting and Formatting Configuration")
    print("=" * 50)

    # Check pyproject.toml exists
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        print("✗ pyproject.toml not found!")
        return 1
    print("✓ pyproject.toml found")

    # Check standalone config files
    ruff_config = root / ".ruff.toml"
    flake8_config = root / ".flake8"
    black_config = root / ".black"  # Optional, usually in pyproject.toml

    if ruff_config.exists():
        print("✓ .ruff.toml found")
    if flake8_config.exists():
        print("✓ .flake8 found")

    # Run checks (dry-run / check-only modes)
    checks = [
        (["ruff", "check", "--output-format=concise", "."], "Ruff check (concise)"),
        (["black", "--check", "--diff", "code/"], "Black format check"),
    ]

    # Only run flake8 if it's installed
    try:
        subprocess.run(["flake8", "--version"], capture_output=True, check=True)
        checks.append((["flake8", "code/"], "Flake8 lint check"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Flake8 not installed, skipping flake8 check")

    results = []
    for cmd, desc in checks:
        results.append(run_command(cmd, desc))

    print("=" * 50)
    if all(results):
        print("✓ All linting and formatting configurations are valid.")
        return 0
    else:
        print("✗ Some checks failed. Please review the configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())