"""Script to run Black formatter on the project code."""
import subprocess
import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run Black formatter.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["code/", "tests/", "scripts/", "data/"],
        help="Paths to format (default: code/, tests/, scripts/, data/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check formatting without modifying files.",
    )
    args = parser.parse_args()

    # Determine the project root (assuming this script is in projects/.../scripts/)
    # We need to run from the project root to respect pyproject.toml
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Ensure we are in the correct directory
    os.chdir(project_root)

    cmd = [sys.executable, "-m", "black"]
    if args.check:
        cmd.append("--check")
    cmd.extend(args.paths)

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("Formatting check passed." if args.check else "Formatting complete.")
    else:
        print("Formatting check failed." if args.check else "Formatting completed with errors.")
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
