"""
Script runner for synthetic data generation.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.synthetic_generator import main

if __name__ == "__main__":
    sys.exit(main())
