"""
Script to run the fallback trait data acquisition (T025b).

This script orchestrates the execution of the traits_fallback module,
which fetches defense trait data from Phenoscape and GBIF when TRY data
is unavailable.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.traits_fallback import main


def main_wrapper():
    """Wrapper to handle script execution."""
    return main()


if __name__ == "__main__":
    sys.exit(main_wrapper())
