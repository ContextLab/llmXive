"""
dry_run_memory_check.py

Thin wrapper that invokes the verification logic defined in
``code/scripts/verify_memory_t011.py``. The script is the public entry point
referenced by task T011 and the quick‑start documentation.
"""

import sys
from scripts.verify_memory_t011 import main

if __name__ == "__main__":
    # Propagate the exit code from ``main`` so the runner can enforce the
    # 7 GB memory gate.
    sys.exit(main())
