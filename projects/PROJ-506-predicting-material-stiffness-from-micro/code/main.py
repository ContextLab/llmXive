"""
Main entry point for the project pipeline.

Currently supports:
- Governance updates (T004): Updates spec.md resolution requirements.
- Future phases will add data generation, training, and evaluation commands.
"""
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Material Stiffness Prediction Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommand for T004: Update Spec Resolution
    parser_update_spec = subparsers.add_parser("update-spec", help="Update spec.md for T004")
    parser_update_spec.add_argument(
        "--force", 
        action="store_true", 
        help="Force update even if patterns seem already updated"
    )

    args = parser.parse_args()

    if args.command == "update-spec":
        # Import the specific task logic
        from code.update_spec_resolution import update_spec_file
        try:
            update_spec_file()
            print("Task T004 completed successfully.")
            return 0
        except Exception as e:
            print(f"Task T004 failed: {e}")
            return 1
    elif args.command is None:
        parser.print_help()
        return 0
    else:
        print(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
