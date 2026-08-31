"""
Runner script for T017.

This script is invoked by the run-book to execute T017.
It imports and calls the main function from generate_standardized_output.py.
"""
import sys
from pathlib import Path

# Add the code directory to the path if necessary (though usually not needed if run from project root)
# The project structure assumes scripts are run from the root.
# However, to be safe, we can add the code directory.
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from generate_standardized_output import main

if __name__ == "__main__":
    main()
