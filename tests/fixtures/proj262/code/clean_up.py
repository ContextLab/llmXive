"""Code cleanup and refactoring sanity check.

This script imports all public symbols from the project's modules to ensure
that the codebase is importable after refactoring. It reports success or
prints any import errors encountered.
"""
from __future__ import annotations

import os
import sys
import traceback

# Ensure the `code` directory is on the import path so that imports like
# `from analysis.confidence_intervals import ...` work.
CODE_DIR = os.path.abspath(os.path.dirname(__file__))
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

# List of import callables to execute. Each entry is a lambda that performs
# the import; wrapping in a lambda delays execution until the loop.
IMPORT_CHECKS = [
    # Analysis modules
    lambda: __import__("analysis.confidence_intervals"),
    lambda: __import__("analysis.generate_performance_plots"),
    lambda: __import__("analysis.generate_significance"),
    lambda: __import__("analysis.statistical_tests"),
    lambda: __import__("analysis.validate_variance"),
    lambda: __import__("analysis.visualize_features"),
    # Attribution modules
    lambda: __import__("attribution.permutation_importance"),
    lambda: __import__("attribution.rank_contributions"),
    lambda: __import__("attribution.saliency_mapping"),
    # Generation scripts
    lambda: __import__("generate_attributions"),
    lambda: __import__("generate_metrics"),
    # Training modules
    lambda: __import__("training.evaluate"),
    lambda: __import__("training.save_checkpoints"),
    lambda: __import__("training.train_gnn"),
    lambda: __import__("training.train_rf"),
    # Utils
    lambda: __import__("utils.validate_urls"),
]

def main() -> int:
    """Run all import checks.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    failed = False
    for idx, check in enumerate(IMPORT_CHECKS, start=1):
        try:
            check()
        except Exception as exc:
            failed = True
            print(f"[ERROR] Import #{idx} failed: {exc}", file=sys.stderr)
            traceback.print_exc()
    if not failed:
        print("✅ All modules imported successfully.")
        return 0
    else:
        print("❌ Some modules failed to import.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
