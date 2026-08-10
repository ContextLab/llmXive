"""
Tests for the data ingestion pipeline.

Tests cover:
- Data download and parsing
- Schema validation
- Missing data handling
- Edge cases (zero votes, anomalies)
- Synthetic data fallback
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import DataIngestionPipeline
from code.discrepancy import DiscrepancyCalculator
from code.exceptions import MissingDataError, DataAcquisitionError
from code.models import validate_output_schema


class TestDataIngestionPipeline(unittest.TestCase):
    """Tests for the DataIngestionPipeline class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pipeline = DataIngestionPipeline(data_dir=self.temp_dir.name)
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
        
    def test_validate_required_fields_valid(self):
        """Test validation with all required fields present."""
        df = pd.DataFrame({
            'precinct_votes': [100, 200, 300],
            'county_total': [1000, 2000, 3000],
            'election_year': [2020, 2020, 2020],
            'jurisdiction_name': ['A', 'B', 'C']
        })
        
        is_valid, missing = self.pipeline.validate_required_fields(df)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
        
    def test_validate_required_fields_missing(self):
        """Test validation with missing required fields."""
        df = pd.DataFrame({
            'precinct_votes': [100, 200],
            'election_year': [2020, 2020]
        })
        
        is_valid, missing = self.pipeline.validate_required_fields(df)
        
        self.assertFalse(is_valid)
        self.assertIn('county_total', missing)
        self.assertIn('jurisdiction_name', missing)
        
    def test_normalize_aggregation_levels(self):
        """Test normalization of column names and types."""
        df = pd.DataFrame({
            'Precinct Votes': [100, 200],
            'County Total': ['1000', '2000'],
            'Election Year': [2020, 2020],
            'Jurisdiction Name': ['A', 'B']
        })
        
        normalized = self.pipeline.normalize_aggregation_levels(df)
        
        # Check column names are lowercased and spaces replaced
        self.assertIn('precinct_votes', normalized.columns)
        self.assertIn('county_total', normalized.columns)
        self.assertIn('election_year', normalized.columns)
        
        # Check types are converted
        self.assertEqual(normalized['county_total'].dtype, np.float64)
        
    def test_handle_zero_county_votes(self):
        """Test filtering of zero county votes."""
        df = pd.DataFrame({
            'precinct_votes': [100, 200, 300],
            'county_total': [1000, 0, 3000],
            'election_year': [2020, 2020, 2020],
            'jurisdiction_name': ['A', 'B', 'C']
        })
        
        filtered = self.pipeline.handle_zero_county_votes(df)
        
        self.assertEqual(len(filtered), 2)
        self.assertNotIn(0, filtered['county_total'].values)
        
    def test_flag_directional_anomalies(self):
        """Test flagging of directional anomalies."""
        df = pd.DataFrame({
            'precinct_sum': [1000, 2000, 3000],
            'county_reported': [1000, 1500, 3000],
            'election_year': [2020, 2020, 2020]
        })
        
        flagged = self.pipeline.flag_directional_anomalies(df)
        
        self.assertIn('directional_anomaly', flagged.columns)
        self.assertEqual(flagged['directional_anomaly'].sum(), 1)  # Only second row
        
    def test_handle_missing_data_flag(self):
        """Test flagging of missing data without imputation."""
        df = pd.DataFrame({
            'precinct_sum': [100, np.nan, 300],
            'county_reported': [1000, 2000, np.nan],
            'election_year': [2020, 2020, 2020]
        })
        
        handled = self.pipeline.handle_missing_data(df, impute=False)
        
        self.assertIn('missing_data', handled.columns)
        self.assertTrue(handled['missing_data'].iloc[1])
        self.assertTrue(handled['missing_data'].iloc[2])
        self.assertFalse(handled['missing_data'].iloc[0])
        
    def test_handle_missing_data_impute(self):
        """Test imputation of missing data."""
        df = pd.DataFrame({
            'precinct_sum': [100, np.nan, 300],
            'county_reported': [1000, 2000, np.nan],
            'election_year': [2020, 2020, 2020]
        })
        
        handled = self.pipeline.handle_missing_data(df, impute=True)
        
        self.assertIn('missing_data', handled.columns)
        self.assertFalse(pd.isna(handled['precinct_sum'].iloc[1]))
        self.assertFalse(pd.isna(handled['county_reported'].iloc[2]))
        
    def test_calculate_discrepancies(self):
        """Test calculation of discrepancy metrics."""
        df = pd.DataFrame({
            'precinct_sum': [1000, 2000, 3000],
            'county_reported': [1000, 1500, 3000],
            'election_year': [2020, 2020, 2020]
        })
        
        result = self.pipeline.calculate_discrepancies(df)
        
        self.assertIn('discrepancy_abs', result.columns)
        self.assertIn('discrepancy_pct', result.columns)
        
        # Check calculations
        self.assertEqual(result['discrepancy_abs'].iloc[0], 0)
        self.assertEqual(result['discrepancy_abs'].iloc[1], 500)
        self.assertAlmostEqual(result['discrepancy_pct'].iloc[1], 33.33, places=1)
        
    def test_generate_synthetic_fallback(self):
        """Test synthetic data generation for validation."""
        synthetic = self.pipeline.generate_synthetic_fallback(n_rows=50)
        
        self.assertEqual(len(synthetic), 50)
        self.assertIn('jurisdiction_name', synthetic.columns)
        self.assertIn('precinct_votes', synthetic.columns)
        self.assertIn('county_total', synthetic.columns)
        
        # Check all values are positive
        self.assertTrue((synthetic['precinct_votes'] > 0).all())
        self.assertTrue((synthetic['county_total'] > 0).all())
        
    def test_validate_output_schema(self):
        """Test output schema validation."""
        df = pd.DataFrame({
            'precinct_sum': [1000, 2000],
            'county_reported': [1000, 1500],
            'discrepancy_abs': [0, 500],
            'discrepancy_pct': [0.0, 33.33],
            'missing_data': [False, False]
        })
        
        # Should not raise
        validate_output_schema(df, ['precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct', 'missing_data'])
        
    def test_process_data_full_pipeline(self):
        """Test the full processing pipeline."""
        df = pd.DataFrame({
            'jurisdiction_name': ['A', 'B', 'C', 'D'],
            'precinct_votes': [100, 200, 300, 400],
            'county_total': [1000, 0, 3000, 4000],  # B has zero
            'election_year': [2020, 2020, 2020, 2020]
        })
        
        result = self.pipeline.process_data(df, election_year=2020)
        
        # Check B was filtered out
        self.assertEqual(len(result), 3)
        self.assertIn('discrepancy_abs', result.columns)
        self.assertIn('discrepancy_pct', result.columns)
        self.assertIn('directional_anomaly', result.columns)
        
class TestDiscrepancyCalculator(unittest.TestCase):
    """Tests for the DiscrepancyCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = DiscrepancyCalculator()
        
    def test_calculate_basic_discrepancies(self):
        """Test basic discrepancy calculation."""
        df = pd.DataFrame({
            'precinct_sum': [1000, 2000, 3000],
            'county_reported': [1000, 1500, 3000]
        })
        
        result = self.calculator.calculate_basic_discrepancies(df)
        
        self.assertEqual(result['discrepancy_abs'].iloc[0], 0)
        self.assertEqual(result['discrepancy_abs'].iloc[1], 500)
        self.assertAlmostEqual(result['discrepancy_pct'].iloc[1], 33.33, places=1)
        
    def test_filter_zero_county_votes(self):
        """Test filtering of zero county votes."""
        df = pd.DataFrame({
            'precinct_sum': [1000, 2000, 3000],
            'county_reported': [1000, 0, 3000]
        })
        
        result = self.calculator.filter_zero_county_votes(df)
        
        self.assertEqual(len(result), 2)
        
    def test_flag_directional_anomalies(self):
        """Test flagging of directional anomalies."""
        df = pd.DataFrame({
            'precinct_sum': [1000, 2000, 3000],
            'county_reported': [1000, 1500, 3000]
        })
        
        result = self.calculator.flag_directional_anomalies(df)
        
        self.assertTrue(result['directional_anomaly'].iloc[1])
        self.assertFalse(result['directional_anomaly'].iloc[0])
        
    def test_calculate_discrepancy_statistics(self):
        """Test calculation of discrepancy statistics."""
        df = pd.DataFrame({
            'discrepancy_abs': [0, 500, -200, 100],
            'discrepancy_pct': [0.0, 33.33, -10.0, 5.0],
            'directional_anomaly': [False, True, False, False],
            'missing_data': [False, False, True, False]
        })
        
        stats = self.calculator.calculate_discrepancy_statistics(df)
        
        self.assertEqual(stats['count'], 4)
        self.assertEqual(stats['mean_abs'], 200)
        self.assertEqual(stats['anomaly_count'], 1)
        self.assertEqual(stats['missing_count'], 1)
        
if __name__ == '__main__':
    unittest.main()
