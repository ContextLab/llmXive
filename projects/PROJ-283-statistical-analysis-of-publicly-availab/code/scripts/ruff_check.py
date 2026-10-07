import subprocess
import sys
from pathlib import Path

def main():
    """
    Run ruff check --select T20 to ensure no print statements remain in the codebase.
    T20 rule in ruff corresponds to 'print' statements (flake8-print).
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)
    
    print(f"Running ruff check --select T20 on {code_dir}...")
    
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "ruff", "check", 
                "--select=T20", 
                str(code_dir)
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Write output to a log file for verification
        log_path = project_root / "data" / "results" / "ruff_check_t20.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, "w") as f:
            f.write(f"Command: ruff check --select T20 {code_dir}\n")
            f.write(f"Return Code: {result.returncode}\n")
            f.write(f"Stdout:\n{result.stdout}\n")
            f.write(f"Stderr:\n{result.stderr}\n")
        
        print(f"Ruff check output saved to: {log_path}")
        
        if result.returncode == 0:
            print("SUCCESS: No print statements (T20) found in the codebase.")
            sys.exit(0)
        else:
            print("FAILURE: Print statements (T20) detected in the codebase:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
            
    except subprocess.TimeoutExpired:
        print("ERROR: Ruff check timed out.")
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: ruff is not installed. Please install it via 'pip install ruff'.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()