"""
Runner script for Task T038: Schema Discovery & Validation.
This script executes the schema discovery and validation process.
"""
import os
import sys
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from schema_discovery import main as schema_discovery_main

if __name__ == "__main__":
  # Change to project root to resolve relative paths correctly
  project_root = code_dir.parent
  os.chdir(project_root)
  
  # Execute the schema discovery and validation
  schema_discovery_main()