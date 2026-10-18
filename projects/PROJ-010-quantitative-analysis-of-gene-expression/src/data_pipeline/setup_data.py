"""
src/data_pipeline/setup_data.py
--------------------------------
Wrapper that re‑exports the full data‑loader implementation located in
``code/data_pipeline/setup_data.py``.  The quick‑start workflow expects the
script to live under ``src/data_pipeline/``; this thin wrapper simply calls
the original ``main`` function so the same logic is used without code
duplication.
"""

# The implementation lives in the ``code`` package to keep the core
# functionality separate from the execution entry‑point expected by the
# quick‑start script.
from code.data_pipeline.setup_data import main

if __name__ == "__main__":
    # Forward all command‑line arguments to the original ``main``.
    main()
