import subprocess
import sys
import os

def main():
    """Run ruff linter on the codebase."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, "code")
    
    print(f"Running ruff on {code_dir}...")
    
    try:
        result = subprocess.run(
            ["ruff", "check", code_dir, "--config", os.path.join(code_dir, ".ruff.toml")],
            check=False,
            capture_output=False
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: 'ruff' is not installed. Please install it via 'pip install ruff'.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running ruff: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
