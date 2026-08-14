"""Script to run Ruff linter on the project code."""
import subprocess
import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run Ruff linter.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["code/", "tests/", "scripts/", "data/"],
        help="Paths to lint (default: code/, tests/, scripts/, data/)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix fixable issues.",
    )
    args = parser.parse_args()

    # Determine the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    os.chdir(project_root)

    cmd = [sys.executable, "-m", "ruff", "check"]
    if args.fix:
        cmd.append("--fix")
    cmd.extend(args.paths)

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("Linting passed.")
    else:
        print("Linting found issues.")
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()