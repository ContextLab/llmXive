"""
Setup Environment Script.

Initializes the project environment by:
1. Checking for .env file existence.
2. Copying .env.example to .env if missing.
3. Creating necessary directory structures.
4. Validating required dependencies (python-dotenv).
"""
import os
import sys
from pathlib import Path
import shutil

# Add project root to path to import utils if needed, though this script is standalone
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
ENV_FILE = PROJECT_ROOT / ".env"
EXAMPLE_ENV = PROJECT_ROOT / "code" / ".env.example"

def check_dotenv():
    """Check if python-dotenv is installed."""
    try:
        import dotenv
        print("✓ python-dotenv is installed.")
        return True
    except ImportError:
        print("⚠ python-dotenv is NOT installed.")
        print("  Installing it allows automatic loading of .env files.")
        print("  Run: pip install python-dotenv")
        return False

def setup_env_file():
    """Create .env from .env.example if it doesn't exist."""
    if not EXAMPLE_ENV.exists():
        print(f"✗ Error: {EXAMPLE_ENV} not found.")
        print("  Please ensure the .env.example template exists.")
        return False

    if not ENV_FILE.exists():
        print(f"Creating {ENV_FILE} from template...")
        shutil.copy(EXAMPLE_ENV, ENV_FILE)
        print("✓ .env file created. Please edit it with your configuration.")
        return True
    else:
        print(f"✓ {ENV_FILE} already exists.")
        return True

def ensure_directories():
    """Ensure required data and log directories exist."""
    dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results",
        PROJECT_ROOT / "figures",
        PROJECT_ROOT / "logs",
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {d}")
        else:
            print(f"Directory exists: {d}")

def main():
    print("=== llmXive Environment Setup ===")
    print(f"Project Root: {PROJECT_ROOT}\n")

    # 1. Check dependency
    check_dotenv()
    print()

    # 2. Setup .env file
    setup_env_file()
    print()

    # 3. Ensure directories
    ensure_directories()
    print()

    print("=== Environment Setup Complete ===")
    print("Next steps:")
    print("1. Edit '.env' to add API keys or custom paths if needed.")
    print("2. Run your pipeline scripts.")

if __name__ == "__main__":
    main()