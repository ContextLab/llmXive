import os
import sys
import logging
from pathlib import Path

# Add the code directory to the path to resolve imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.download_nist_juliet import main as juliet_main

def main():
    """Wrapper to run the Juliet download script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        success = juliet_main()
        if not success:
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error in Juliet download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
