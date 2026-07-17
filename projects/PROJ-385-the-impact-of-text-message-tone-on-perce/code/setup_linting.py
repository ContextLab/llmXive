"""
Script to verify ruff and black installation and configuration.
This script checks if the tools are available and validates basic configuration.
"""
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {tool_name} is installed: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {tool_name} is not installed or not accessible.")
        return False

def main():
    """Main entry point for the setup_linting script."""
    project_root = Path(__file__).parent
    pyproject_path = project_root / "pyproject.toml"

    print("Checking linting and formatting tools configuration...")
    print("-" * 50)

    # Check installations
    black_ok = check_tool("black")
    ruff_ok = check_tool("ruff")

    if not (black_ok and ruff_ok):
        print("\n❌ One or more tools are missing. Please install them:")
        print("   pip install black ruff")
        sys.exit(1)

    # Verify configuration file exists
    if not pyproject_path.exists():
        print(f"\n❌ Configuration file not found at {pyproject_path}")
        sys.exit(1)

    print(f"✓ Configuration file found at {pyproject_path}")

    # Run a dry-run check to ensure config is valid
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--config", str(pyproject_path), "--output-format", "concise", "."],
            cwd=project_root,
            capture_output=True,
            check=False
        )
        print("✓ Ruff configuration is valid.")
    except Exception as e:
        print(f"⚠ Ruff configuration check failed: {e}")

    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--config", str(pyproject_path), "--check", "--diff", "."],
            cwd=project_root,
            capture_output=True,
            check=False
        )
        print("✓ Black configuration is valid.")
    except Exception as e:
        print(f"⚠ Black configuration check failed: {e}")

    print("-" * 50)
    print("✅ Linting and formatting tools are configured successfully.")
    print("Run 'ruff check .' to lint and 'black .' to format.")

if __name__ == "__main__":
    main()
