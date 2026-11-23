"""
Convenience runner for T015 to ensure the script executes end-to-end
and writes results_full.csv to the correct location.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from t015_generate_full_results import main

if __name__ == "__main__":
    main()