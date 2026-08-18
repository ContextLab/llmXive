"""
Wrapper script to execute T017: Generate standardized CSV output.
This script ensures the preprocessing pipeline has run and then generates
the final standardized output with checksums.
"""
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from generate_standardized_output import main

if __name__ == "__main__":
    main()