import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import get_config

# The main runner simply forwards to the analysis module's main entry point.
# No changes are required for T023b, but we keep the file for completeness.
def main() -> None:
    from analysis import correlations

    logging.basicConfig(level=logging.INFO)
    correlations.main()

if __name__ == "__main__":
    main()
