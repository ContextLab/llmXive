import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path if not already there
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.evaluation.metrics import calculate_coverage

class TestCoverageCalculation:
    """Tests for the calculate_coverage function (T024)."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock forecasts data
        self.forecasts_data = {
            'election_date': pd.date_range('2020-01-01', periods=10, freq='D'),
            'lower_95': [40.0 - i * 0.5 for i in range(10)],
            'upper_95': [44.0 + i * 0.5 for i in range(10)],
            'candidate': ['A'] * 10
        }
        
        # Create mock outcomes data
        # 7 out of 10 should be within CI (70% coverage)
        self.outcomes_data = {
            'election_date': pd.date_range('2020-01-01', periods=10, freq='D'),
            'actual_vote_share': [41.0, 42.0, 43.0, 38.0, 44.0, 45.0, 42.5, 41.5, 40.0, 43.0],
            'candidate': ['A'] * 10
        }
        
        self.forecasts_path = os.path.join(self.temp_dir, "forecasts.csv")
        self.outcomes_path = os.path.join(self.temp_dir, "outcomes.csv")
        self.output_path = os.path.join(self.temp_dir, "coverage_results.csv")
        
        pd.DataFrame(self.forecasts_data).to_csv(self.forecasts_path, index=False)
        pd.DataFrame(self.outcomes_data).to_csv(self.outcomes_path, index=False)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_coverage_calculation_basic(self):
        """Test basic coverage calculation."""
        results = calculate_coverage(
            forecasts_path=self.forecasts_path,
            outcomes_path=self.outcomes_path,
            output_path=self.output_path
        )
        
        assert 'coverage_rate' in results
        assert 'total_predictions' in results
        assert 'within_ci_count' in results
        assert 'outside_ci_count' in results
        
        # Check specific values
        # Forecasts: [40, 40.5, ..., 44.5] vs [44, 44.5, ..., 48.5]
        # Actuals: [41, 42, 43, 38, 44, 45, 42.5, 41.5, 40, 43]
        # Within CI check:
        # 41 in [40, 44.5]? Yes
        # 42 in [40.5, 45]? Yes
        # 43 in [41, 45.5]? Yes
        # 38 in [41.5, 46]? No (38 < 41.5)
        # 44 in [42, 46.5]? Yes
        # 45 in [42.5, 47]? Yes
        # 42.5 in [43, 47.5]? No (42.5 < 43)
        # 41.5 in [43.5, 48]? No (41.5 < 43.5)
        # 40 in [44, 48.5]? No (40 < 44)
        # 43 in [44.5, 49]? No (43 < 44.5)
        # Wait, let me recalculate based on the data generation:
        # lower_95 = [40, 39.5, 39, 38.5, 38, 37.5, 37, 36.5, 36, 35.5]
        # upper_95 = [44.5, 44.5, 44.5, 44.5, 44.5, 44.5, 44.5, 44.5, 44.5, 44.5] 
        # Wait, the list comprehension was: [40.0 - i * 0.5 for i in range(10)]
        # i=0: 40.0
        # i=1: 39.5
        # i=2: 39.0
        # ...
        # i=9: 35.5
        # upper_95 = [44.0 + i * 0.5 for i in range(10)]
        # i=0: 44.0
        # i=1: 44.5
        # ...
        # i=9: 48.5
        
        # Actuals: [41, 42, 43, 38, 44, 45, 42.5, 41.5, 40, 43]
        # Check 41 in [40, 44]: Yes
        # Check 42 in [39.5, 44.5]: Yes
        # Check 43 in [39, 45]: Yes
        # Check 38 in [38.5, 45.5]: No (38 < 38.5)
        # Check 44 in [38, 46]: Yes
        # Check 45 in [37.5, 46.5]: Yes
        # Check 42.5 in [37, 47]: Yes
        # Check 41.5 in [36.5, 47.5]: Yes
        # Check 40 in [36, 48]: Yes
        # Check 43 in [35.5, 48.5]: Yes
        
        # So 9 out of 10 should be within CI
        assert results['total_predictions'] == 10
        assert results['within_ci_count'] == 9
        assert results['outside_ci_count'] == 1
        assert abs(results['coverage_rate'] - 0.9) < 1e-6

    def test_coverage_with_custom_columns(self):
        """Test coverage calculation with custom column names."""
        # Create data with different column names
        custom_forecasts = {
            'date': pd.date_range('2020-01-01', periods=5, freq='D'),
            'lower_ci': [40.0, 41.0, 42.0, 43.0, 44.0],
            'upper_ci': [50.0, 51.0, 52.0, 53.0, 54.0]
        }
        custom_outcomes = {
            'date': pd.date_range('2020-01-01', periods=5, freq='D'),
            'actual': [45.0, 46.0, 47.0, 48.0, 49.0]
        }
        
        custom_forecast_path = os.path.join(self.temp_dir, "custom_forecasts.csv")
        custom_outcome_path = os.path.join(self.temp_dir, "custom_outcomes.csv")
        
        pd.DataFrame(custom_forecasts).to_csv(custom_forecast_path, index=False)
        pd.DataFrame(custom_outcomes).to_csv(custom_outcome_path, index=False)
        
        results = calculate_coverage(
            forecasts_path=custom_forecast_path,
            outcomes_path=custom_outcome_path,
            lower_col='lower_ci',
            upper_col='upper_ci',
            actual_col='actual',
            output_path=None
        )
        
        assert results['coverage_rate'] == 1.0  # All within CI
        assert results['total_predictions'] == 5

    def test_coverage_empty_data(self):
        """Test coverage calculation with no overlapping data."""
        # Create data with no matching dates
        no_overlap_forecasts = {
            'election_date': pd.date_range('2020-01-01', periods=5, freq='D'),
            'lower_95': [40.0] * 5,
            'upper_95': [50.0] * 5
        }
        no_overlap_outcomes = {
            'election_date': pd.date_range('2021-01-01', periods=5, freq='D'),
            'actual_vote_share': [45.0] * 5
        }
        
        no_overlap_forecast_path = os.path.join(self.temp_dir, "no_overlap_forecasts.csv")
        no_overlap_outcome_path = os.path.join(self.temp_dir, "no_overlap_outcomes.csv")
        
        pd.DataFrame(no_overlap_forecasts).to_csv(no_overlap_forecast_path, index=False)
        pd.DataFrame(no_overlap_outcomes).to_csv(no_overlap_outcome_path, index=False)
        
        results = calculate_coverage(
            forecasts_path=no_overlap_forecast_path,
            outcomes_path=no_overlap_outcome_path,
            output_path=None
        )
        
        assert results['coverage_rate'] == 0.0
        assert results['total_predictions'] == 0
        assert results['within_ci_count'] == 0

    def test_coverage_output_file_created(self):
        """Test that output file is created when path is provided."""
        results = calculate_coverage(
            forecasts_path=self.forecasts_path,
            outcomes_path=self.outcomes_path,
            output_path=self.output_path
        )
        
        assert os.path.exists(self.output_path)
        output_df = pd.read_csv(self.output_path)
        assert len(output_df) == 1
        assert 'coverage_rate' in output_df.columns