import sys
from pathlib import Path


def main():
    """
    Main entry point for running the setup sequence.
    
    This script orchestrates the installation of dependencies and configuration
    required for the project. It calls the SRA Toolkit installer as part of
    the setup process.
    """
    print("=" * 60)
    print("Project Setup Sequence")
    print("=" * 60)
    
    # Import and run SRA Toolkit installer
    try:
        from install_sra_toolkit import main as install_sra_main
        exit_code = install_sra_main()
        if exit_code != 0:
            print("\n⚠ SRA Toolkit installation had issues.")
            print("  You may need to complete this manually.")
    except ImportError as e:
        print(f"\n⚠ Could not import SRA Toolkit installer: {e}")
        print("  Please ensure install_sra_toolkit.py is in the code/ directory.")
    
    print("\n" + "=" * 60)
    print("Setup sequence complete.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())