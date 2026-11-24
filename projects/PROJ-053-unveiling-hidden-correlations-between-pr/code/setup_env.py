import subprocess
from pathlib import Path
from config import get_results_dir, ensure_directories

def main():
    """
    Captures the current environment's pinned versions via pip freeze 
    and writes them to the results directory for provenance verification.
    """
    results_dir = Path(get_results_dir())
    ensure_directories([results_dir])
    freeze_path = results_dir / "env_freeze.txt"
    
    try:
        result = subprocess.run(["pip", "freeze"], capture_output=True, text=True, check=True)
        with open(freeze_path, "w") as f:
            f.write(result.stdout)
        print(f"Environment freeze successfully written to {freeze_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run pip freeze: {e}")
        exit(1)

if __name__ == "__main__":
    main()