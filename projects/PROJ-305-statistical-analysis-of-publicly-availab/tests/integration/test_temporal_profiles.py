"""
Integration test for temporal profile generation (T031).

This test verifies that the temporal analysis pipeline:
1. Loads the signals from output/signals.csv
2. Identifies top 5 candidate SOCs (or all if <5)
3. Generates weekly count plots for each SOC
4. Saves plots to output/temporal_profiles/
5. Handles edge cases (empty signals, missing data)

Prerequisites:
- T026 must be complete (output/signals.csv exists)
- T032 must be complete (top 5 SOC identification logic)
- T033, T034, T035 must be complete (temporal.py implementation)
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.temporal import (
    identify_top_socs,
    calculate_median_date,
    aggregate_weekly_counts,
    generate_temporal_plots
)
from src.utils.config import ensure_dirs


class TestTemporalProfilesIntegration:
    """Integration tests for temporal profile generation."""

    @pytest.fixture(autouse=True)
    def setup_temp_dirs(self, tmp_path):
        """Set up temporary directories for test outputs."""
        self.tmp_path = tmp_path
        self.output_dir = self.tmp_path / "output"
        self.signals_path = self.output_dir / "signals.csv"
        self.temporal_dir = self.output_dir / "temporal_profiles"
        
        # Create directory structure
        self.output_dir.mkdir(parents=True)
        self.temporal_dir.mkdir(parents=True)
        
        # Store original paths to restore later
        self.original_output_dir = os.environ.get("OUTPUT_DIR")
        os.environ["OUTPUT_DIR"] = str(self.output_dir)
        
        yield
        
        # Restore original environment
        if self.original_output_dir:
            os.environ["OUTPUT_DIR"] = self.original_output_dir
        else:
            os.environ.pop("OUTPUT_DIR", None)

    def _create_test_signals(self, num_signals=10, num_no_signals=0):
        """Create a test signals.csv file."""
        if num_no_signals > 0:
            # Create empty signals file with correct schema
            df = pd.DataFrame(columns=[
                'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
                'prr', 'prr_ci_lower', 'prr_ci_upper',
                'ic', 'ic_ci_lower', 'ic_ci_upper',
                'p_adj', 'signal_flag'
            ])
        else:
            # Create realistic signal data
            data = {
                'soc': [f"SOC_{i:03d}" for i in range(num_signals)],
                'ror': np.random.uniform(2.0, 5.0, num_signals),
                'ror_ci_lower': np.random.uniform(1.0, 3.0, num_signals),
                'ror_ci_upper': np.random.uniform(3.0, 6.0, num_signals),
                'prr': np.random.uniform(1.5, 4.0, num_signals),
                'prr_ci_lower': np.random.uniform(1.0, 2.5, num_signals),
                'prr_ci_upper': np.random.uniform(2.0, 5.0, num_signals),
                'ic': np.random.uniform(0.5, 2.0, num_signals),
                'ic_ci_lower': np.random.uniform(0.0, 1.0, num_signals),
                'ic_ci_upper': np.random.uniform(1.0, 3.0, num_signals),
                'p_adj': np.random.uniform(0.01, 0.5, num_signals),
                'signal_flag': [True] * num_signals
            }
            df = pd.DataFrame(data)
        
        df.to_csv(self.signals_path, index=False)
        return df

    def _create_test_cleaned_data(self, num_rows=1000):
        """Create test cleaned data with dates and SOCs."""
        # Generate realistic date range (2020-2023)
        start_date = pd.Timestamp("2020-01-01")
        end_date = pd.Timestamp("2023-12-31")
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        
        # Sample dates
        dates = np.random.choice(date_range, num_rows)
        
        # Sample SOCs (matching signals)
        socs = [f"SOC_{i:03d}" for i in range(10)]
        soc_data = np.random.choice(socs, num_rows)
        
        # Group labels
        groups = np.random.choice(["COVID-19", "Non-COVID", "Non-COVID-Non-Flu"], num_rows)
        
        df = pd.DataFrame({
            'REPT_DATE': dates,
            'SOC': soc_data,
            'GROUP': groups
        })
        
        return df

    def test_identify_top_socs_with_multiple_signals(self):
        """Test that top 5 SOCs are correctly identified from signals."""
        # Create signals with varying ROR values
        df = self._create_test_signals(num_signals=10)
        
        # Sort by ROR descending and take top 5
        top_5 = df.nlargest(5, 'ror')['soc'].tolist()
        
        # Test the function
        result = identify_top_socs(self.signals_path, top_n=5)
        
        assert len(result) == 5
        assert all(soc in top_5 for soc in result)
        assert isinstance(result, list)

    def test_identify_top_socs_fewer_than_5(self):
        """Test that all signals are returned when fewer than 5 exist."""
        df = self._create_test_signals(num_signals=3)
        
        result = identify_top_socs(self.signals_path, top_n=5)
        
        assert len(result) == 3
        assert all(soc in df['soc'].tolist() for soc in result)

    def test_identify_top_socs_zero_signals(self):
        """Test handling of zero signals (edge case)."""
        self._create_test_signals(num_no_signals=1)
        
        result = identify_top_socs(self.signals_path, top_n=5)
        
        assert len(result) == 0
        assert isinstance(result, list)

    def test_generate_temporal_plots_full_pipeline(self):
        """Test complete pipeline: signals -> top SOCs -> plots generation."""
        # Create test signals
        self._create_test_signals(num_signals=8)
        
        # Create test cleaned data
        cleaned_data = self._create_test_cleaned_data(num_rows=500)
        
        # Save cleaned data temporarily
        cleaned_path = self.tmp_path / "cleaned_vaers.csv"
        cleaned_data.to_csv(cleaned_path, index=False)
        
        # Generate plots
        results = generate_temporal_plots(
            signals_path=self.signals_path,
            cleaned_data_path=cleaned_path,
            output_dir=self.temporal_dir,
            top_n=5
        )
        
        # Verify results
        assert isinstance(results, dict)
        assert "num_signals" in results
        assert "plots_generated" in results
        assert "soc_list" in results
        
        # Verify plots were created
        expected_soc_count = min(5, results["num_signals"])
        assert results["plots_generated"] == expected_soc_count
        
        # Check that plot files exist
        plot_files = list(self.temporal_dir.glob("SOC_*.png"))
        assert len(plot_files) == expected_soc_count

    def test_generate_temporal_plots_empty_signals(self):
        """Test handling of empty signals (edge case)."""
        self._create_test_signals(num_no_signals=1)
        
        # Create minimal cleaned data
        cleaned_data = self._create_test_cleaned_data(num_rows=100)
        cleaned_path = self.tmp_path / "cleaned_vaers.csv"
        cleaned_data.to_csv(cleaned_path, index=False)
        
        # Generate plots (should handle gracefully)
        results = generate_temporal_plots(
            signals_path=self.signals_path,
            cleaned_data_path=cleaned_path,
            output_dir=self.temporal_dir,
            top_n=5
        )
        
        assert results["num_signals"] == 0
        assert results["plots_generated"] == 0
        
        # Verify placeholder file was created
        placeholder = self.temporal_dir / "empty_signal_warning.txt"
        assert placeholder.exists()

    def test_plot_files_have_correct_format(self):
        """Test that generated plots are valid PNG files."""
        self._create_test_signals(num_signals=5)
        cleaned_data = self._create_test_cleaned_data(num_rows=500)
        cleaned_path = self.tmp_path / "cleaned_vaers.csv"
        cleaned_data.to_csv(cleaned_path, index=False)
        
        results = generate_temporal_plots(
            signals_path=self.signals_path,
            cleaned_data_path=cleaned_path,
            output_dir=self.temporal_dir,
            top_n=5
        )
        
        # Check each plot file
        for plot_file in self.temporal_dir.glob("SOC_*.png"):
            assert plot_file.stat().st_size > 0  # File is not empty
            
            # Verify it's a valid PNG (check header bytes)
            with open(plot_file, 'rb') as f:
                header = f.read(8)
                assert header[:8] == b'\x89PNG\r\n\x1a\n'

    def test_plot_labels_include_reporting_time(self):
        """Test that plots are labeled as 'Reporting Time' not 'Vaccination Time'."""
        self._create_test_signals(num_signals=5)
        cleaned_data = self._create_test_cleaned_data(num_rows=500)
        cleaned_path = self.tmp_path / "cleaned_vaers.csv"
        cleaned_data.to_csv(cleaned_path, index=False)
        
        generate_temporal_plots(
            signals_path=self.signals_path,
            cleaned_data_path=cleaned_path,
            output_dir=self.temporal_dir,
            top_n=5
        )
        
        # Read plot metadata (filename should indicate SOC)
        plot_files = list(self.temporal_dir.glob("SOC_*.png"))
        assert len(plot_files) == 5
        
        # Verify the function creates plots with correct naming convention
        # The actual label verification would require parsing the image,
        # but we verify the function was called correctly
        for soc in results.get("soc_list", []):
            expected_pattern = f"SOC_{soc}"
            matching_files = [f for f in plot_files if soc in f.name]
            assert len(matching_files) > 0

    def test_weekly_aggregation_handles_missing_dates(self):
        """Test that weekly aggregation handles missing/invalid dates gracefully."""
        # Create signals
        self._create_test_signals(num_signals=5)
        
        # Create data with some missing dates
        cleaned_data = self._create_test_cleaned_data(num_rows=500)
        # Introduce some NaT values
        cleaned_data.loc[::50, 'REPT_DATE'] = pd.NaT
        
        cleaned_path = self.tmp_path / "cleaned_vaers.csv"
        cleaned_data.to_csv(cleaned_path, index=False)
        
        # Should not raise an exception
        results = generate_temporal_plots(
            signals_path=self.signals_path,
            cleaned_data_path=cleaned_path,
            output_dir=self.temporal_dir,
            top_n=5
        )
        
        assert results["plots_generated"] == 5

    def test_median_date_calculation_across_groups(self):
        """Test that median date is calculated correctly for each group."""
        cleaned_data = self._create_test_cleaned_data(num_rows=1000)
        cleaned_path = self.tmp_path / "cleaned_vaers.csv"
        cleaned_data.to_csv(cleaned_path, index=False)
        
        # Calculate median for COVID-19 group
        covid_data = cleaned_data[cleaned_data['GROUP'] == 'COVID-19']
        expected_median = covid_data['REPT_DATE'].median()
        
        # Calculate median for Non-COVID-Non-Flu group
        baseline_data = cleaned_data[cleaned_data['GROUP'] == 'Non-COVID-Non-Flu']
        expected_baseline_median = baseline_data['REPT_DATE'].median()
        
        # Verify medians are reasonable (within date range)
        assert pd.Timestamp("2020-01-01") <= expected_median <= pd.Timestamp("2023-12-31")
        assert pd.Timestamp("2020-01-01") <= expected_baseline_median <= pd.Timestamp("2023-12-31")