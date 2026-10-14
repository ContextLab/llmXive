"""
Simple verification test that ensures required third‑party packages are
importable after `pip install -r requirements.txt` has been executed.
"""
def test_lightgbm_import():
    """
    LightGBM is listed in requirements.txt; importing it proves the
    installation succeeded.
    """
    import lightgbm
    # The presence of the LGBMRegressor class indicates a functional import
    assert hasattr(lightgbm, "LGBMRegressor")

def test_textstat_import():
    """
    textstat is also required; verify it can be imported.
    """
    import textstat
    assert callable(getattr(textstat, "flesch_kincaid_grade", None))

def test_datasets_import():
    """
    The HuggingFace datasets library must be importable.
    """
    import datasets
    assert hasattr(datasets, "load_dataset")