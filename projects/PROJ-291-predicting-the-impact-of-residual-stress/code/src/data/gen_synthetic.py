"""
code/src/data/gen_synthetic.py
--------------------------------
Wrapper module that re‑exports the deterministic synthetic dataset generator
defined in the top‑level ``src.data.gen_synthetic`` package.

The project’s quick‑start and test suite import ``src.data.gen_synthetic``.
For completeness – and to satisfy the task specification that the script
lives under ``code/src/data`` – we provide a thin wrapper that simply calls
the original implementation.
"""

# The original implementation lives in the top‑level ``src`` package.
# Import it and expose its ``main`` entry point.
from src.data.gen_synthetic import main as _original_main

def main(argv=None) -> None:
    """
    CLI entry point used by ``python -m code.src.data.gen_synthetic``.
    Delegates to the real generator in ``src.data.gen_synthetic``.
    """
    # ``argv`` is accepted for compatibility with the typical ``main`` signature
    # but is ignored because the underlying generator does not require command‑line
    # arguments.
    _original_main()

if __name__ == "__main__":
    main()