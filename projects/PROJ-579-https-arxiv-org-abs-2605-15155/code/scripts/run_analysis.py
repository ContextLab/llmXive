"""
T036a Execution Wrapper
Runs the vendored code structure analysis.
"""
import sys
from pathlib import Path

# Add parent to path for imports if needed, though this script is standalone
# We assume the analyze script is in code/scripts/
script_path = Path(__file__).parent / "analyze_vendored_structure.py"

if __name__ == "__main__":
    import subprocess
    result = subprocess.run([sys.executable, str(script_path)], check=False)
    sys.exit(result.returncode)
