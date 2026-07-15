"""
Package marker for the `code` directory.

Adding this file makes `code` a proper Python package, allowing imports such as
`from code.simulation.logging_config import ...` to work when `code/main.py` is
executed as a script (e.g., `python code/main.py`). This resolves the
`ModuleNotFoundError: No module named 'code.simulation'` observed during the
run‑book execution.

No additional functionality is required here; the presence of this file is
sufficient for correct package resolution.
"""