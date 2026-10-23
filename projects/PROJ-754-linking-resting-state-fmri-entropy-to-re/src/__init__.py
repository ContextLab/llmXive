"""
Top‑level ``src`` package that re‑exports the actual source tree located at
``code/src``.  This shim enables imports such as ``import src.data.qc`` that
the existing test suite expects.
"""
import sys
from pathlib import Path

# Resolve the path to the real implementation package.
_real_src_path = Path(__file__).resolve().parent / "code" / "src"
if str(_real_src_path) not in sys.path:
    sys.path.insert(0, str(_real_src_path))

# After adjusting ``sys.path`` the sub‑modules can be imported normally.
# No further symbols are defined here.
