"""
Standalone script to run the complexity scorer pipeline.
This script computes complexity scores for all generated variants.
"""
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from entropy.scorer import main

if __name__ == "__main__":
    main()