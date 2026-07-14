"""
Pytest configuration and shared fixtures for llmXive project.
"""
import os
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Ensure code/ directory is importable
code_dir = project_root / "code"
if code_dir.exists() and str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Optional: Set test environment variables
os.environ.setdefault("PYTEST_CURRENT_TEST_PROJECT", "llmXive")
