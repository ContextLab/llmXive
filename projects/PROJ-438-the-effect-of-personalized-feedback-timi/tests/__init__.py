"""
Test suite for PROJ-438: The Effect of Personalized Feedback Timing on Skill Acquisition.

This package contains unit tests, integration tests, and validation scripts
for the research pipeline.
"""

import os
import sys

# Add the project root to the path for imports during testing
# This allows tests to import from the 'code' directory directly
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
code_dir = os.path.join(project_root, "code")
if os.path.isdir(code_dir) and code_dir not in sys.path:
    sys.path.insert(0, code_dir)