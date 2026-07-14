"""
Test suite to verify that all required dependencies specified in T002
are installed and importable in the Python 3.11 environment.
"""
import pytest

def test_pandas_import():
    import pandas as pd
    assert pd.__version__ is not None

def test_scipy_import():
    import scipy
    assert scipy.__version__ is not None

def test_pytest_import():
    import pytest
    assert pytest.__version__ is not None

def test_pyyaml_import():
    import yaml
    assert yaml.__version__ is not None

def test_jsonschema_import():
    import jsonschema
    assert jsonschema.__version__ is not None

def test_datasets_import():
    from datasets import load_dataset
    assert load_dataset is not None

def test_tqdm_import():
    from tqdm import tqdm
    assert tqdm is not None

def test_numpy_import():
    import numpy as np
    assert np.__version__ is not None

def test_statsmodels_import():
    import statsmodels
    assert statsmodels.__version__ is not None