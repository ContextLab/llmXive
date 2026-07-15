import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import filter_constructed_wetlands, filter_nutrient_removal_metrics

class TestFilterConstructedWetlands:
    def test_filter_cw(self):
        data = {
            'sample_id': ['s1', 's2', 's3'],
            'site_type': ['Constructed Wetland', 'Lake', 'CW-System']
        }
        df = pd.DataFrame(data)
        filtered, excluded = filter_constructed_wetlands(df)
        assert len(filtered) == 2
        assert excluded == 1

    def test_no_cw(self):
        data = {
            'sample_id': ['s1', 's2'],
            'site_type': ['Lake', 'River']
        }
        df = pd.DataFrame(data)
        filtered, excluded = filter_constructed_wetlands(df)
        assert len(filtered) == 0
        assert excluded == 2

class TestFilterNutrientRemoval:
    def test_filter_np(self):
        data = {
            'sample_id': ['s1', 's2', 's3'],
            'total_n': [10.0, np.nan, 12.0],
            'total_p': [5.0, 6.0, np.nan]
        }
        df = pd.DataFrame(data)
        filtered, excluded = filter_nutrient_removal_metrics(df)
        # Only s1 has both N and P
        assert len(filtered) == 1
        assert excluded == 2

    def test_no_np(self):
        data = {
            'sample_id': ['s1', 's2'],
            'temperature': [20.0, 21.0],
            'ph': [7.0, 7.5]
        }
        df = pd.DataFrame(data)
        filtered, excluded = filter_nutrient_removal_metrics(df)
        assert len(filtered) == 0
        assert excluded == 2
