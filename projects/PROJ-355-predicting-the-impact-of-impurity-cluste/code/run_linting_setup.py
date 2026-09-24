"""
Runner script for linting setup and verification.
Orchestrates the installation and configuration of ruff and black.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config_linting import main as config_linting_main
from linting_setup import main as linting_setup_main


def main() -> int:
    """
    Main entry point for running the full linting setup.

    Returns:
        0 on success, 1 on failure.
    """
    print("=" * 60)
    print("Running Linting Setup")
    print("=" * 60)

    # Step 1: Install tools if missing
    print("\n[Step 1/2] Installing tools...")
    install_status = linting_setup_main()

    if install_status != 0:
        print("\n✗ Tool installation failed.")
        return 1

    # Step 2: Verify configuration
    print("\n[Step 2/2] Verifying configuration...")
    verify_status = config_linting_main()

    if verify_status != 0:
        print("\n✗ Configuration verification failed.")
        return 1

    print("\n" + "=" * 60)
    print("✓ Linting setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Run 'ruff check .' to check for linting issues")
    print("  - Run 'black .' to format code")
    print("  - Run 'ruff format .' to format code (ruff 0.1.0+)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
