"""
Entry point wrapper for T015 to ensure it runs as a standalone script.
This script calls the main logic in t015_generate_full_results.py.
"""
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from t015_generate_full_results import main

if __name__ == "__main__":
    main()