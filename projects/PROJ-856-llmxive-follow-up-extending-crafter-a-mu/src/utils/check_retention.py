"""
Thin wrapper that forwards to ``src.analysis.retention_check``.
The quick‑start documentation historically referenced this module, so we keep it
for backward compatibility.
"""

import sys
from src.analysis.retention_check import main as _main

if __name__ == "__main__":
    sys.exit(_main())
