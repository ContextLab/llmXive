"""
Basic sanity test that the data package exports the expected function.
"""

from code.data import save_raw_and_cleaned_data  # type: ignore

def test_export_exists():
    assert callable(save_raw_and_cleaned_data)
