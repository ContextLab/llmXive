"""Runner script for T015 to ensure it can be executed independently."""
import subprocess
import sys
from pathlib import Path

def main():
    """Run T015 experiment."""
    script_path = Path(__file__).parent / "t015_generate_full_results.py"
    result = subprocess.run([sys.executable, str(script_path)], check=True)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())