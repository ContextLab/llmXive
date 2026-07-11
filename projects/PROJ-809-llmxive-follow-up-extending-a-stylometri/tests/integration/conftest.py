"""
Pytest configuration for integration tests.
"""
import os
import sys
from pathlib import Path

# Ensure the code directory is in the path
root = Path(__file__).parent.parent.parent
code_dir = root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Fixtures can be defined here if shared across tests