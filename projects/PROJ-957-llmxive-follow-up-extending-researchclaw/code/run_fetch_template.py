"""
Runner script for T009b: Fetch and Normalize Template.

This script executes the template fetcher to:
1. Read the verified URL from assets/templates/verified_template_url.txt
2. Fetch the content from that URL
3. Extract the protocol content
4. Save it to assets/templates/TEMPLATE-001-v1.0.md
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.templates.fetcher import main

if __name__ == "__main__":
    sys.exit(main())
