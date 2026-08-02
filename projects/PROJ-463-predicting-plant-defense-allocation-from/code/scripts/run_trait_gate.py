"""
Script wrapper for T038: Trait data gate task.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.traits_gate import main

if __name__ == '__main__':
    sys.exit(main())