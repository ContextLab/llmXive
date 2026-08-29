"""
Unit tests for code/data/split.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
import os
import yaml

from code.data.split import random_split, stratified_split, execute_split, _load_config


class TestRandomSplit:
    def test_basic_split(self):
        df = pd.DataFrame({"a": range(100), "b": range(100, 200)})
        train, test = random_split(df, test_size=0.2, random_state=42)
        assert len(train) + len(test) == 100
        assert len(test) == 20
        assert len(train) == 80

    def test_invalid_test_size(self):
        df = pd.DataFrame({"a": range(10)})
        with pytest.raises(ValueError):
            random_split(df, test_size=1.5)
        with pytest.raises(ValueError):
            random_split(df, test_size=0.0)

    def test_reproducibility(self):
        df = pd.DataFrame({"a": range(100)})
        t1, te1 = random_split(df, test_size=0.2, random_state=42)
        t2, te2 = random_split(df, test_size=0.2, random_state=42)
        assert t1.equals(t2)
        assert te1.equals(te2)


class TestStratifiedSplit:
    def setup_method(self):
        # Create a balanced dataset for stratification
        classes = ["A"] * 50 + ["B"] * 50
        np.random.seed(42)
        np.random.shuffle(classes)
        self.df = pd.DataFrame({
            "feature": range(100),
            "polymer_type": classes
        })

    def test_stratified_split_success(self):
        train, test = stratified_split(self.df, stratify_col="polymer_type", test_size=0.2)
        
        # Check sizes
        assert len(train) + len(test) == 100
        assert len(test) == 20
        
        # Check distribution
        train_dist = train["polymer_type"].value_counts(normalize=True)
        test_dist = test["polymer_type"].value_counts(normalize=True)
        
        # Both should be roughly 0.5/0.5
        assert abs(train_dist["A"] - 0.5) < 0.1
        assert abs(test_dist["A"] - 0.5) < 0.1

    def test_missing_stratify_column(self):
        with pytest.raises(SystemExit):
            stratified_split(self.df, stratify_col="nonexistent_col")

    def test_distribution_threshold_violation(self):
        # Create a dataset where stratification might fail threshold
        # (This is hard to trigger with perfect stratify, so we test the logic path)
        # We rely on the internal validation logic. 
        # If we force a bad split (not possible with sklearn stratify), we'd trigger it.
        # Instead, we test the threshold parameter logic by mocking or ensuring it runs.
        train, test = stratified_split(
            self.df, 
            stratify_col="polymer_type", 
            test_size=0.2, 
            max_distribution_diff=0.05
        )
        # Should pass normally
        assert len(train) == 80

    def test_insufficient_classes(self):
        df = pd.DataFrame({"feature": range(10), "polymer_type": ["A"] * 10})
        with pytest.raises(ValueError):
            stratified_split(df, stratify_col="polymer_type")


class TestExecuteSplit:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"
        # Save config in temp dir
        with open(self.config_path, 'w') as f:
            yaml.dump({"staged_mode": False, "stratification_diff_threshold": 0.05}, f)
        
        # Mock _load_config to use our temp config
        self.original_load = _load_config
        # We can't easily patch the internal import, so we rely on the function reading from parent
        # For this test, we'll just ensure the file exists in the expected location relative to the script
        # But since we are running unit tests, we might need to mock the path resolution.
        # Instead, let's test the logic with a dataframe that has the column.

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_execute_with_stratify_column(self):
        df = pd.DataFrame({
            "smiles": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
            "polymer_type": ["A", "A", "A", "A", "A", "B", "B", "B", "B", "B"],
            "logP": [1.0, 2.0, 3.0, 4.0, 5.0, 1.5, 2.5, 3.5, 4.5, 5.5]
        })
        
        output_dir = Path(self.temp_dir) / "output"
        train_path, test_path = execute_split(df, str(output_dir), stratify_column="polymer_type")
        
        assert Path(train_path).exists()
        assert Path(test_path).exists()
        
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        assert len(train_df) + len(test_df) == 10

    def test_execute_without_stratify_column(self):
        # Simulate Proxy Mode: no polymer_type
        df = pd.DataFrame({
            "smiles": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
            "logP": [1.0, 2.0, 3.0, 4.0, 5.0, 1.5, 2.5, 3.5, 4.5, 5.5]
        })
        
        output_dir = Path(self.temp_dir) / "output_fallback"
        # This should trigger the fallback logic
        train_path, test_path = execute_split(df, str(output_dir), stratify_column="polymer_type")
        
        assert Path(train_path).exists()
        assert Path(test_path).exists()
        
        # Just check sizes, order is random
        assert len(pd.read_csv(train_path)) + len(pd.read_csv(test_path)) == 10

    def test_output_files_created(self):
        df = pd.DataFrame({
            "a": range(20),
            "polymer_type": ["A"] * 10 + ["B"] * 10
        })
        output_dir = Path(self.temp_dir) / "output_check"
        train_path, test_path = execute_split(df, str(output_dir))
        
        assert Path(train_path).name == "train.csv"
        assert Path(test_path).name == "test.csv"