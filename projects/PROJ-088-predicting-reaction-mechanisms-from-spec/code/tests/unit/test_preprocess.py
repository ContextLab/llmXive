import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.ingestion.preprocess import normalize_spectrum, bin_spectrum, detect_outliers, validate_class_balance, preprocess_dataset

class TestNormalizeSpectrum:
    def test_minmax_normalization(self):
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        normalized = normalize_spectrum(data, method="minmax")
        expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        np.testing.assert_array_almost_equal(normalized, expected)

    def test_l2_normalization(self):
        data = np.array([3.0, 4.0])
        normalized = normalize_spectrum(data, method="l2")
        expected = np.array([0.6, 0.8])
        np.testing.assert_array_almost_equal(normalized, expected)

    def test_constant_spectrum(self):
        data = np.array([5.0, 5.0, 5.0])
        normalized = normalize_spectrum(data, method="minmax")
        expected = np.zeros_like(data)
        np.testing.assert_array_almost_equal(normalized, expected)

    def test_empty_spectrum(self):
        data = np.array([])
        with pytest.raises(ValueError):
            normalize_spectrum(data)

class TestBinSpectrum:
    def test_bin_spectrum_basic(self):
        # Create a simple spectrum: 4000 to 1000
        freqs = np.linspace(4000, 1000, 100)
        spectrum = np.ones(100) * 10.0
        
        binned = bin_spectrum(spectrum, freqs, n_bins=10, freq_range=(4000, 1000))
        
        assert len(binned) == 10
        # All values should be close to 10.0 since input is constant
        assert np.allclose(binned, 10.0, atol=1e-5)

    def test_bin_spectrum_mismatched_lengths(self):
        freqs = np.array([4000, 3000, 2000])
        spectrum = np.array([10.0, 20.0])
        with pytest.raises(ValueError):
            bin_spectrum(spectrum, freqs)

    def test_bin_spectrum_out_of_range(self):
        # Frequencies outside the bin range should be handled by interpolation (clamped)
        freqs = np.array([5000, 4000, 3000, 2000])
        spectrum = np.array([0.0, 1.0, 1.0, 0.0])
        
        # Bin range 4000-2000
        binned = bin_spectrum(spectrum, freqs, n_bins=4, freq_range=(4000, 2000))
        assert len(binned) == 4

class TestDetectOutliers:
    def test_extreme_variance(self):
        # Create a dataframe with one row having extreme variance
        data = {
            "bin_0": [10.0, 10.0, 10.0, 100.0], # Last one is outlier
            "bin_1": [10.0, 10.0, 10.0, 10.0],
            "bin_2": [10.0, 10.0, 10.0, 10.0]
        }
        df = pd.DataFrame(data)
        outliers = detect_outliers(df, ["bin_0", "bin_1", "bin_2"], threshold=2.0)
        
        assert len(outliers) > 0
        assert any(o["type"] == "extreme_variance" for o in outliers)

    def test_missing_range(self):
        # Create a dataframe with one row having near-zero mean
        data = {
            "bin_0": [10.0, 0.0],
            "bin_1": [10.0, 0.0],
            "bin_2": [10.0, 0.0]
        }
        df = pd.DataFrame(data)
        outliers = detect_outliers(df, ["bin_0", "bin_1", "bin_2"], threshold=2.0)
        
        # Should detect the row with 0.0 mean as potential missing range
        assert any(o["type"] == "missing_range" for o in outliers)

class TestValidateClassBalance:
    def test_balanced_classes(self):
        df = pd.DataFrame({"label": ["A"] * 100, "val": [1]*100})
        result = validate_class_balance(df, "label", min_samples=50)
        assert result["valid"] is True
        assert len(result["flags"]) == 0

    def test_imbalanced_classes(self):
        df = pd.DataFrame({"label": ["A"] * 100 + ["B"] * 10, "val": [1]*110})
        result = validate_class_balance(df, "label", min_samples=50)
        assert result["valid"] is False
        assert any("Class 'B'" in flag for flag in result["flags"])

    def test_missing_label_column(self):
        df = pd.DataFrame({"other": [1, 2, 3]})
        result = validate_class_balance(df, "label", min_samples=50)
        assert result["valid"] is False
        assert "error" in result

class TestPreprocessDataset:
    def test_end_to_end(self):
        # Create a temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create a simple wide-format dataset
            # 4000 to 1000 in 100 steps
            freqs = np.linspace(4000, 1000, 100)
            cols = [f"freq_{int(f)}" for f in freqs]
            data = {col: [10.0] * 5 for col in cols}
            data["label"] = ["A", "B", "A", "B", "A"]
            df = pd.DataFrame(data)
            df.to_csv(f.name, index=False)
            input_path = f.name
        
        output_path = tempfile.mktemp(suffix='.csv')
        
        try:
            preprocess_dataset(input_path, output_path, n_bins=10, freq_range=(4000, 1000), label_col="label", min_samples=1)
            
            assert os.path.exists(output_path)
            result_df = pd.read_csv(output_path)
            
            # Check columns
            assert "label" in result_df.columns
            assert len([c for c in result_df.columns if c.startswith("bin_")]) == 10
            assert len(result_df) == 5
            
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)