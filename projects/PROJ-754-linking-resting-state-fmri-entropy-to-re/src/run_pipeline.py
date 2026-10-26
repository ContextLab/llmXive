"""
Wrapper module that re‑exports the ``main`` entry point from the actual implementation
located in ``code.src.run_pipeline``.  This allows the test suite (and users) to import
``src.run_pipeline`` while keeping the full implementation under the ``code/src`` tree.
"""

from code.src.run_pipeline import main

if __name__ == "__main__":
    main()
