"""
Script to run memory profiling on the pipeline components.

This script serves as a convenient entry point to profile memory usage
of the ingestion and modeling pipelines.
"""
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from profile_memory import main

if __name__ == "__main__":
    sys.exit(main())