"""
CLI entry point for running the trait fallback data acquisition (T025b).

This script orchestrates the fallback trait fetch from Phenoscape and GBIF
for species missing from the primary TRY database.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.traits_fallback import main

if __name__ == "__main__":
    sys.exit(main())
