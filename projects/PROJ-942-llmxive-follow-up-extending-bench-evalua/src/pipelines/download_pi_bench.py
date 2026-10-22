"""
Wrapper script that forwards to the implementation in ``code/pipelines/download_pi_bench.py``.
The quickstart reference expects the script to live under ``src/pipelines``.
"""

import runpy
import sys
from pathlib import Path

# Ensure the repository root is on the import path (usually it is)
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Execute the main function from the actual implementation
runpy.run_path(str(Path(__file__).parent.parent.parent / "code" / "pipelines" / "download_pi_bench.py"))

# The above script performs all work and exits. No further code is needed.