"""
Script to run Task T026: Variance Correlation Analysis.
"""
import sys
from pathlib import Path

# Add project root to path if needed (though usually run from root)
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.variance_correlation import main

if __name__ == "__main__":
    main()