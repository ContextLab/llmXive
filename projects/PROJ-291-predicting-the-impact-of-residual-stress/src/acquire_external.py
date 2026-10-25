"""
src/acquire_external.py
-----------------------
Wrapper module to expose the acquisition script located in
``code/src/acquire_external.py`` under the ``src`` package namespace.
This allows test modules (e.g., ``tests/test_acquire.py``) to import
``src.acquire_external`` and call its ``main`` function.
"""
from code.src.acquire_external import main  # noqa: F401

if __name__ == "__main__":
    # When executed as a script (e.g., ``python -m src.acquire_external``)
    # forward to the real implementation.
    main()