"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))
