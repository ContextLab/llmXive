"""
Verify that core dependencies can be imported.
"""

def test_import_pandas():
    import pandas
    # Ensure pandas is importable and has a version attribute.
    assert hasattr(pandas, "__version__")
