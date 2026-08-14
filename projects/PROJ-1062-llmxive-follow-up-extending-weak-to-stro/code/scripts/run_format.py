import subprocess
import sys
import os
import argparse

def main():
    """Run black formatter on the codebase."""
    parser = argparse.ArgumentParser(description="Format code with black and ruff-format")
    parser.add_argument("--check", action="store_true", help="Check formatting only, do not modify files")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, "code")
    
    print(f"Running formatter on {code_dir}...")
    
    # Run ruff format (preferred over black directly as per .pre-commit-config)
    try:
        cmd = ["ruff", "format", code_dir, "--config", os.path.join(code_dir, ".ruff.toml")]
        if args.check:
            cmd.append("--check")
        
        result = subprocess.run(cmd, check=False, capture_output=False)
        
        if result.returncode != 0:
            if args.check:
                print("\nFormatting check failed. Run 'python code/scripts/run_format.py' to fix.")
            sys.exit(result.returncode)
        else:
            if args.check:
                print("All files are properly formatted.")
            else:
                print("Formatting complete.")
                
    except FileNotFoundError:
        print("Error: 'ruff' is not installed. Please install it via 'pip install ruff'.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running formatter: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()