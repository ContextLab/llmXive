import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from features import (
    calculate_lempel_ziv_complexity, 
    calculate_permutation_entropy, 
    save_metrics_to_csv
)

class TestComplexityMetrics:
    
    def test_lzc_constant_signal(self):
        """LZC of a constant signal should be very low."""
        signal = np.ones(1000)
        lzc = calculate_lempel_ziv_complexity(signal)
        assert 0.0 <= lzc <= 0.1, f"Constant signal LZC should be near 0, got {lzc}"
        
    def test_lzc_random_signal(self):
        """LZC of random signal should be higher than constant."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        lzc = calculate_lempel_ziv_complexity(signal)
        assert lzc > 0.1, f"Random signal LZC should be > 0.1, got {lzc}"
        
    def test_permutation_entropy_constant(self):
        """Permutation entropy of constant signal should be 0."""
        signal = np.ones(1000)
        pe = calculate_permutation_entropy(signal)
        assert np.isclose(pe, 0.0, atol=0.1), f"Constant signal PE should be ~0, got {pe}"
        
    def test_permutation_entropy_random(self):
        """Permutation entropy of random signal should be positive."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        pe = calculate_permutation_entropy(signal)
        assert pe > 0.0, f"Random signal PE should be > 0, got {pe}"

    def test_save_metrics_csv(self, tmp_path):
        """Test that save_metrics_to_csv creates a valid file."""
        metrics = [
            {"participant_id": "sub-01", "channel": "Cz", "lzc": 0.5, "pe": 1.2},
            {"participant_id": "sub-01", "channel": "Fz", "lzc": 0.4, "pe": 1.1}
        ]
        output_file = tmp_path / "test_metrics.csv"
        save_metrics_to_csv(metrics, output_file)
        
        assert output_file.exists(), "Output file was not created"
        df = pd.read_csv(output_file)
        assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
        assert "lzc" in df.columns, "Missing 'lzc' column"
        assert "pe" in df.columns, "Missing 'pe' column"
        assert "channel" in df.columns, "Missing 'channel' column"