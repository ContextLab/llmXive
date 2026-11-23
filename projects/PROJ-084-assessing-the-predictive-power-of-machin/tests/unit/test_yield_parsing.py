"""
Unit tests for yield parsing functionality in sanitize.py
"""

import pytest
from preprocessing.sanitize import parse_yield

class TestYieldParsing:
    """Tests for parse_yield function"""
    
    def test_single_integer_yield(self):
        """Test parsing single integer yield"""
        assert parse_yield('85') == 85.0
        assert parse_yield('50') == 50.0
    
    def test_single_float_yield(self):
        """Test parsing single float yield"""
        assert parse_yield('85.5') == 85.5
        assert parse_yield('50.25') == 50.25
    
    def test_percentage_suffix(self):
        """Test parsing yield with percentage sign"""
        assert parse_yield('85%') == 85.0
        assert parse_yield('50.5%') == 50.5
    
    def test_range_with_hyphen(self):
        """Test parsing yield range with hyphen"""
        assert parse_yield('50-70') == 60.0
        assert parse_yield('30-40') == 35.0
    
    def test_range_with_spaces(self):
        """Test parsing yield range with spaces"""
        assert parse_yield('50 - 70') == 60.0
        assert parse_yield('30 - 40') == 35.0
    
    def test_range_with_en_dash(self):
        """Test parsing yield range with en-dash"""
        assert parse_yield('50–70') == 60.0
        assert parse_yield('30–40') == 35.0
    
    def test_range_with_em_dash(self):
        """Test parsing yield range with em-dash"""
        assert parse_yield('50—70') == 60.0
        assert parse_yield('30—40') == 35.0
    
    def test_nan_yield(self):
        """Test parsing NaN yield"""
        import pandas as pd
        assert parse_yield(pd.NA) is None
        assert parse_yield(None) is None
        assert parse_yield('') is None
    
    def test_malformed_yield(self):
        """Test parsing malformed yield values"""
        assert parse_yield('invalid') is None
        assert parse_yield('abc-def') is None
        assert parse_yield('150') is None  # Out of range
        assert parse_yield('-10') is None  # Negative
    
    def test_edge_case_zero(self):
        """Test parsing zero yield"""
        assert parse_yield('0') == 0.0
        assert parse_yield('0%') == 0.0
    
    def test_edge_case_hundred(self):
        """Test parsing hundred percent yield"""
        assert parse_yield('100') == 100.0
        assert parse_yield('100%') == 100.0
    
    def test_range_with_zero(self):
        """Test parsing range starting at zero"""
        assert parse_yield('0-50') == 25.0
    
    def test_range_with_hundred(self):
        """Test parsing range ending at hundred"""
        assert parse_yield('50-100') == 75.0
    
    def test_numeric_input(self):
        """Test parsing numeric input (not string)"""
        assert parse_yield(85) == 85.0
        assert parse_yield(50.5) == 50.5
    
    def test_range_numeric(self):
        """Test parsing range as numeric would fail (expected)"""
        # Ranges are typically strings, but test behavior
        assert parse_yield(60) == 60.0  # Single value