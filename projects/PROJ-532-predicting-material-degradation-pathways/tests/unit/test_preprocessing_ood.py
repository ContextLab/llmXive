import pandas as pd
import numpy as np
import pytest
import os
import json
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from preprocessing import classify_alloy_family, perform_ood_split, _perform_stratified_random_split

class TestOodSplit:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir)

    def test_classify_alloy_family_hea(self):
        """Test High-Entropy Alloy classification."""
        # HEA: 5+ elements > 5%, max < 40%
        data = {
            'Fe': 20.0, 'Cr': 20.0, 'Ni': 20.0, 'Co': 20.0, 'Mn': 20.0
        }
        row = pd.Series(data)
        assert classify_alloy_family(row) == "High-Entropy Alloys"

    def test_classify_alloy_family_stainless(self):
        """Test Stainless Steel classification."""
        # Stainless: Cr > 10.5%, Fe < 85%
        data = {
            'Fe': 70.0, 'Cr': 18.0, 'Ni': 8.0, 'C': 0.1
        }
        row = pd.Series(data)
        assert classify_alloy_family(row) == "Stainless Steels"

    def test_classify_alloy_family_carbon_steel(self):
        """Test Carbon Steel classification."""
        # Carbon Steel: Fe 80-98%, low alloying
        data = {
            'Fe': 97.0, 'C': 0.5, 'Mn': 1.0, 'Si': 1.0
        }
        row = pd.Series(data)
        assert classify_alloy_family(row) == "Carbon Steels"

    def test_ood_split_multiple_families(self):
        """Test OOD split when >= 2 families exist."""
        # Create a dataset with HEA and Stainless
        data = []
        # 10 HEA samples
        for i in range(10):
            data.append({
                'Fe': 20.0, 'Cr': 20.0, 'Ni': 20.0, 'Co': 20.0, 'Mn': 20.0,
                'target': 'pitting'
            })
        # 10 Stainless samples
        for i in range(10):
            data.append({
                'Fe': 70.0, 'Cr': 18.0, 'Ni': 8.0, 'C': 0.1,
                'target': 'scc'
            })
        
        df = pd.DataFrame(data)
        train_df, test_df, report = perform_ood_split(df)
        
        assert report['fallback_triggered'] == False
        assert report['split_method'] == 'alloy_family_ood'
        assert report['held_out_family'] is not None
        # All test samples should belong to the held out family
        assert len(test_df) > 0
        assert len(train_df) > 0
        assert train_df['alloy_family'].nunique() == 1 or len(train_df) == 0 # Only one family in train (the other one)
        # Check that test set is purely one family
        assert test_df['alloy_family'].nunique() == 1

    def test_ood_split_fallback_single_family(self):
        """Test OOD split fallback when < 2 families exist."""
        # Create a dataset with only HEA
        data = []
        for i in range(20):
            data.append({
                'Fe': 20.0, 'Cr': 20.0, 'Ni': 20.0, 'Co': 20.0, 'Mn': 20.0,
                'target': 'pitting'
            })
        
        df = pd.DataFrame(data)
        train_df, test_df, report = perform_ood_split(df)
        
        assert report['fallback_triggered'] == True
        assert report['split_method'] == 'stratified_random'
        assert len(train_df) + len(test_df) == len(df)
        assert len(test_df) > 0 # Should have a test set even if fallback

    def test_ood_split_report_contents(self):
        """Verify the report contains required fields."""
        data = []
        for i in range(10):
            data.append({'Fe': 20.0, 'Cr': 20.0, 'Ni': 20.0, 'Co': 20.0, 'Mn': 20.0})
        for i in range(10):
            data.append({'Fe': 70.0, 'Cr': 18.0, 'Ni': 8.0, 'C': 0.1})
        
        df = pd.DataFrame(data)
        _, _, report = perform_ood_split(df)
        
        required_keys = ['total_records', 'unique_families', 'family_counts', 
                         'split_method', 'fallback_triggered', 'held_out_family',
                         'train_count', 'test_count', 'note']
        for key in required_keys:
            assert key in report, f"Missing key in report: {key}"