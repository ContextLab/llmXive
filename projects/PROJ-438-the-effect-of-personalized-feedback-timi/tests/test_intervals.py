"""
Unit tests for interval calculation precision (Task T021).

Verifies that the interval calculation logic in code/compute_intervals.py
produces results with a precision of at least 0.1 hours.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add the project code directory to the path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from compute_intervals import calculate_intervals


class TestIntervalCalculationPrecision:
    """Tests to ensure interval calculations are precise to >= 0.1 hours."""

    def test_precision_to_01_hours(self):
        """
        Test that calculated intervals have precision of at least 0.1 hours.
        
        Creates synthetic events with known time differences and verifies
        the calculated intervals match the expected precision.
        """
        # Create a sample dataset with known time differences
        # 0.5 hours = 30 minutes
        # 1.5 hours = 90 minutes
        # 2.25 hours = 135 minutes
        
        data = {
            'learner_id': ['L001', 'L001', 'L001', 'L002', 'L002'],
            'submission_time': [
                datetime(2023, 1, 1, 10, 0, 0),
                datetime(2023, 1, 1, 12, 0, 0),
                datetime(2023, 1, 1, 14, 0, 0),
                datetime(2023, 1, 1, 9, 0, 0),
                datetime(2023, 1, 1, 11, 30, 0)
            ],
            'response_time': [
                datetime(2023, 1, 1, 10, 30, 0),  # 0.5 hours
                datetime(2023, 1, 1, 13, 30, 0),  # 1.5 hours
                datetime(2023, 1, 1, 16, 15, 0),  # 2.25 hours
                datetime(2023, 1, 1, 10, 0, 0),   # 1.0 hours
                datetime(2023, 1, 1, 12, 0, 0)    # 0.5 hours
            ]
        }
        
        df = pd.DataFrame(data)
        
        # Calculate intervals
        result = calculate_intervals(df)
        
        # Verify the intervals are calculated with sufficient precision
        # Check that we have the expected number of rows
        assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
        
        # Verify the intervals match expected values (within floating point tolerance)
        expected_intervals = [0.5, 1.5, 2.25, 1.0, 0.5]
        calculated_intervals = result['interval_hours'].tolist()
        
        for i, (expected, calculated) in enumerate(zip(expected_intervals, calculated_intervals)):
            # Allow for small floating point errors, but require at least 0.1h precision
            # The difference should be much less than 0.1
            diff = abs(expected - calculated)
            assert diff < 0.01, f"Interval {i} precision error: expected {expected}, got {calculated}, diff={diff}"
            
            # Verify the decimal place is meaningful (not just 0 or 1)
            # 0.5, 1.5, 2.25, 1.0, 0.5 all have at least one decimal place
            assert calculated % 0.1 < 0.01 or abs(calculated % 0.1 - 0.1) < 0.01, \
                f"Interval {i} does not have required 0.1h precision: {calculated}"

    def test_sub_hour_intervals(self):
        """
        Test that intervals less than 1 hour are calculated with 0.1h precision.
        """
        # Create events with very small time differences
        data = {
            'learner_id': ['L001', 'L001', 'L001'],
            'submission_time': [
                datetime(2023, 1, 1, 10, 0, 0),
                datetime(2023, 1, 1, 10, 10, 0),  # 10 minutes = 0.1667h
                datetime(2023, 1, 1, 10, 20, 0)   # 20 minutes = 0.3333h
            ],
            'response_time': [
                datetime(2023, 1, 1, 10, 6, 0),   # 6 minutes = 0.1h
                datetime(2023, 1, 1, 10, 16, 0),  # 6 minutes = 0.1h
                datetime(2023, 1, 1, 10, 26, 0)   # 6 minutes = 0.1h
            ]
        }
        
        df = pd.DataFrame(data)
        result = calculate_intervals(df)
        
        # All intervals should be exactly 0.1 hours (6 minutes)
        expected = 0.1
        for calculated in result['interval_hours']:
            assert abs(calculated - expected) < 0.001, \
                f"Sub-hour interval precision failed: expected {expected}, got {calculated}"

    def test_large_interval_precision(self):
        """
        Test that large intervals maintain 0.1h precision.
        """
        # Create events with large time differences
        data = {
            'learner_id': ['L001'],
            'submission_time': [datetime(2023, 1, 1, 0, 0, 0)],
            'response_time': [datetime(2023, 1, 3, 12, 30, 0)]  # 60.5 hours
        }
        
        df = pd.DataFrame(data)
        result = calculate_intervals(df)
        
        expected = 60.5
        calculated = result['interval_hours'].iloc[0]
        
        assert abs(calculated - expected) < 0.01, \
            f"Large interval precision failed: expected {expected}, got {calculated}"

    def test_edge_case_exact_boundary(self):
        """
        Test intervals that fall exactly on 0.1h boundaries.
        """
        # Create events with intervals that are exact multiples of 0.1h
        test_cases = [
            (0.1, 6),   # 6 minutes
            (0.2, 12),  # 12 minutes
            (0.5, 30),  # 30 minutes
            (1.0, 60),  # 60 minutes
            (2.5, 150), # 150 minutes
            (10.0, 600) # 600 minutes
        ]
        
        for expected_hours, expected_minutes in test_cases:
            data = {
                'learner_id': ['L001'],
                'submission_time': [datetime(2023, 1, 1, 10, 0, 0)],
                'response_time': [datetime(2023, 1, 1, 10, expected_minutes, 0)]
            }
            
            df = pd.DataFrame(data)
            result = calculate_intervals(df)
            calculated = result['interval_hours'].iloc[0]
            
            # Verify the calculation is precise to at least 0.1h
            assert abs(calculated - expected_hours) < 0.01, \
                f"Edge case failed for {expected_hours}h: got {calculated}"

    def test_nan_handling_with_precision(self):
        """
        Test that NaN values are handled correctly and don't affect precision of valid values.
        """
        data = {
            'learner_id': ['L001', 'L002', 'L003'],
            'submission_time': [
                datetime(2023, 1, 1, 10, 0, 0),
                datetime(2023, 1, 1, 11, 0, 0),
                None  # Missing submission time
            ],
            'response_time': [
                datetime(2023, 1, 1, 10, 30, 0),  # 0.5h
                datetime(2023, 1, 1, 11, 15, 0),  # 0.25h
                datetime(2023, 1, 1, 12, 0, 0)    # Missing submission, should be NaN
            ]
        }
        
        df = pd.DataFrame(data)
        result = calculate_intervals(df)
        
        # Check that valid intervals are still precise
        valid_intervals = result['interval_hours'].dropna()
        assert len(valid_intervals) == 2, "Expected 2 valid intervals"
        
        # Verify precision of valid intervals
        expected = [0.5, 0.25]
        for i, val in enumerate(valid_intervals):
            assert abs(val - expected[i]) < 0.01, \
                f"Valid interval {i} precision failed: expected {expected[i]}, got {val}"

    def test_rounding_behavior(self):
        """
        Test that the rounding behavior maintains 0.1h precision.
        """
        # Create an interval that would result in many decimal places
        # 7 minutes = 0.116666... hours
        data = {
            'learner_id': ['L001'],
            'submission_time': [datetime(2023, 1, 1, 10, 0, 0)],
            'response_time': [datetime(2023, 1, 1, 10, 7, 0)]
        }
        
        df = pd.DataFrame(data)
        result = calculate_intervals(df)
        calculated = result['interval_hours'].iloc[0]
        
        # The result should be approximately 0.1167 hours
        # Verify it has at least 0.1h precision (i.e., not rounded to 0 or 0.2)
        assert calculated > 0.1 and calculated < 0.2, \
            f"Rounding destroyed precision: expected ~0.1167, got {calculated}"
        
        # Verify the decimal part is meaningful
        decimal_part = calculated % 0.1
        assert decimal_part > 0.01 or abs(decimal_part - 0.1) < 0.01, \
            f"Decimal precision lost: {calculated}"