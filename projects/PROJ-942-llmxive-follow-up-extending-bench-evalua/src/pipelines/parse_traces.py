"""
src/pipelines/parse_traces.py

Thin wrapper that forwards execution to the implementation located at
``code/pipelines/parse_traces.py``. This keeps the public CLI path used in
the project's quickstart (`src/pipelines/...`) while re‑using the fully
tested parsing logic under ``code/pipelines``.
"""

import pathlib
import runpy
import sys

def _run_underlying():
    """
    Resolve the path to the actual implementation script and execute it
    with the current ``sys.argv`` unchanged, so that argument parsing
    behaves exactly as if the user ran the original file directly.
    """
    # The repository layout is:
    #   <repo_root>/code/pipelines/parse_traces.py
    #   <repo_root>/src/pipelines/parse_traces.py   (this wrapper)
    # Compute the sibling ``code/pipelines`` directory relative to this file.
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    impl_path = repo_root / "code" / "pipelines" / "parse_traces.py"
    if not impl_path.is_file():
        raise FileNotFoundError(f"Implementation script not found at {impl_path}")
    # Execute the implementation as a script (its __name__ will be "__main__").
    runpy.run_path(str(impl_path), run_name="__main__")

if __name__ == "__main__":
    # Preserve the original command‑line arguments; the underlying script
    # expects the same ``sys.argv`` format.
    _run_underlying()