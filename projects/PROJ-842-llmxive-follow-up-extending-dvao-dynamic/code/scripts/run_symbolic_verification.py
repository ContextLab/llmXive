"""
Script to execute the symbolic math engine verification (T026b).

This script runs the verification logic defined in src/derivation/symbolic_verification.py
and ensures the log file logs/symbolic_verification.log is generated.

Usage:
    python scripts/run_symbolic_verification.py
"""
import os
import sys
import argparse

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def main():
    parser = argparse.ArgumentParser(description="Run symbolic verification for DVAO noise scaling.")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose logging")
    args = parser.parse_args()

    try:
        from src.derivation.symbolic_verification import main as verification_main
        exit_code = verification_main()
        sys.exit(exit_code)
    except ImportError as e:
        print(f"Error importing verification module: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
