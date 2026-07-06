"""
Script to run the T036 verification: Extracted fields exist for > 95% of valid pages.
"""
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tests.integration.test_extractor_field_coverage import main

if __name__ == "__main__":
    sys.exit(main())