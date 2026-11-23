"""
Unit tests to verify that required dependencies can be imported.
This ensures requirements.txt is sufficient for the project.
"""
import pytest

def test_numpy_import():
    import numpy

def test_pandas_import():
    import pandas

def test_scipy_import():
    import scipy

def test_statsmodels_import():
    import statsmodels

def test_pingouin_import():
    import pingouin

def test_streamlit_import():
    import streamlit

def test_requests_import():
    import requests

def test_pytest_import():
    import pytest

def test_yaml_import():
    import yaml