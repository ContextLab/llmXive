"""
code/tests/test_pipeline_entry.py
---------------------------------
Unit test verifying that the public pipeline API is correctly wired
and returns the expected artifact metadata.
"""

from code.pipeline.run import run

def test_pipeline_entry():
    """
    Verify that run() executes without exception and returns a 
    dictionary containing the required path keys.
    """
    # The function should execute without raising.
    result = run()
    
    # Assert the return type and required keys.
    assert isinstance(result, dict), "run() must return a dictionary"
    
    required_keys = {"raw_path", "features_path", "model_path"}
    assert required_keys.issubset(result.keys()), \
        f"Return dict missing required keys. Expected {required_keys}, got {result.keys()}"