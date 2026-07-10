"""
Root-level pytest configuration.
Ensures the project structure is recognized and standard fixtures are available.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Re-export fixtures from code/conftest.py if needed, or define root-level ones
# Most fixtures are defined in code/conftest.py to be shared with code logic if necessary,
# but pytest discovers them from the tests/ directory hierarchy.
# We include this file to ensure the tests directory is a proper package.
pass
