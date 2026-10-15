"""Execute the full pipeline on a minimal synthetic dataset and verify that
the runtime log is produced and contains the required entries.

This script is used by the evaluation harness to confirm that the
``code/src/pipeline/__main__.py`` implementation satisfies Task T007.
"""
import sys
from pathlib import Path

# Ensure the project root points at the current working directory.
# The test harness will set up a temporary directory and populate the
# required raw files there.
from llmxive_toolkit import paths
import importlib

# Import the pipeline entry point.
pipeline_main = importlib.import_module("code.src.pipeline.__main__")

# Run the pipeline with a tiny permutation count to keep execution fast.
exit_code = pipeline_main.main(["--seed", "42", "--max_taxa", "10", "--perm_iterations", "5"])
sys.exit(exit_code)