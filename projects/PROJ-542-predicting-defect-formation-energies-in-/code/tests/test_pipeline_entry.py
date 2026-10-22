"""
code/tests/test_pipeline_entry.py
---------------------------------

Unit test that verifies the pipeline module can be imported and that the
``run`` function executes without raising an exception.  The test does not
invoke the full end‑to‑end workflow (that is exercised by the quick‑start
integration test); it merely checks that the public API is present.
"""

import importlib

def test_pipeline_entry():
    """
    Import the pipeline module and ensure that a ``run`` callable exists.
    Execute ``run()`` and assert that it returns ``None`` without raising.
    """
    pipeline = importlib.import_module("src.pipeline.run")
    assert hasattr(pipeline, "run"), "pipeline module must expose a 'run' function"
    # The function should complete without raising; any exception will cause the test to fail.
    result = pipeline.run()
    assert result is None, "pipeline.run() should return None on success"
