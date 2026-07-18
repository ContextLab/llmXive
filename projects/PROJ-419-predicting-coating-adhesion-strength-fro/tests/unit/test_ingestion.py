import pytest
import pandas as pd
from datetime import datetime, timedelta
from ingestion import resolve_duplicates

class TestResolveDuplicates:
    """
    Unit tests for the duplicate resolution logic in ingestion.py.
    
    Resolves duplicates based on:
    1. Most recent date (primary criterion)
    2. Highest sample count (tie-breaker if dates are equal)
    """

    def setup_method(self):
        """Prepare test data for duplicate resolution scenarios."""
        self.base_date = datetime(2023, 1, 1)
        
    def test_no_duplicates_returns_original(self):
        """Test that records with unique IDs are returned unchanged."""
        data = [
            {"id": "1", "date": "2023-01-01", "sample_count": 10, "value": 100},
            {"id": "2", "date": "2023-01-02", "sample_count": 20, "value": 200},
        ]
        df = pd.DataFrame(data)
        
        result = resolve_duplicates(df)
        
        assert len(result) == 2
        assert result.iloc[0]["id"] == "1"
        assert result.iloc[1]["id"] == "2"

    def test_duplicate_resolved_by_most_recent_date(self):
        """Test that among duplicates, the one with the most recent date is kept."""
        data = [
            {"id": "1", "date": "2023-01-01", "sample_count": 10, "value": 100},
            {"id": "1", "date": "2023-06-01", "sample_count": 15, "value": 150},
            {"id": "1", "date": "2023-03-01", "sample_count": 12, "value": 120},
        ]
        df = pd.DataFrame(data)
        
        result = resolve_duplicates(df)
        
        assert len(result) == 1
        assert result.iloc[0]["date"] == "2023-06-01"
        assert result.iloc[0]["value"] == 150
        assert result.iloc[0]["sample_count"] == 15

    def test_duplicate_resolved_by_sample_count_on_date_tie(self):
        """Test that if dates are equal, the record with the highest sample count is kept."""
        data = [
            {"id": "1", "date": "2023-01-01", "sample_count": 10, "value": 100},
            {"id": "1", "date": "2023-01-01", "sample_count": 25, "value": 250},
            {"id": "1", "date": "2023-01-01", "sample_count": 15, "value": 150},
        ]
        df = pd.DataFrame(data)
        
        result = resolve_duplicates(df)
        
        assert len(result) == 1
        assert result.iloc[0]["date"] == "2023-01-01"
        assert result.iloc[0]["sample_count"] == 25
        assert result.iloc[0]["value"] == 250

    def test_multiple_groups_of_duplicates(self):
        """Test resolution when there are multiple distinct groups of duplicates."""
        data = [
            {"id": "1", "date": "2023-01-01", "sample_count": 10, "value": 100},
            {"id": "1", "date": "2023-06-01", "sample_count": 15, "value": 150},
            {"id": "2", "date": "2023-02-01", "sample_count": 20, "value": 200},
            {"id": "2", "date": "2023-02-01", "sample_count": 30, "value": 300},
            {"id": "3", "date": "2023-03-01", "sample_count": 5, "value": 50},
        ]
        df = pd.DataFrame(data)
        
        result = resolve_duplicates(df)
        
        assert len(result) == 3
        
        # Check group 1: most recent date
        row_1 = result[result["id"] == "1"].iloc[0]
        assert row_1["date"] == "2023-06-01"
        assert row_1["value"] == 150
        
        # Check group 2: same date, highest sample count
        row_2 = result[result["id"] == "2"].iloc[0]
        assert row_2["date"] == "2023-02-01"
        assert row_2["sample_count"] == 30
        assert row_2["value"] == 300
        
        # Check group 3: single record
        row_3 = result[result["id"] == "3"].iloc[0]
        assert row_3["value"] == 50

    def test_empty_dataframe(self):
        """Test handling of an empty dataframe."""
        df = pd.DataFrame(columns=["id", "date", "sample_count", "value"])
        
        result = resolve_duplicates(df)
        
        assert len(result) == 0
        assert list(result.columns) == ["id", "date", "sample_count", "value"]

    def test_single_record(self):
        """Test handling of a dataframe with a single record."""
        data = [{"id": "1", "date": "2023-01-01", "sample_count": 10, "value": 100}]
        df = pd.DataFrame(data)
        
        result = resolve_duplicates(df)
        
        assert len(result) == 1
        assert result.iloc[0]["value"] == 100

    def test_date_parsing_integrity(self):
        """Test that the function correctly parses ISO date strings."""
        data = [
            {"id": "1", "date": "2023-12-31", "sample_count": 10, "value": 100},
            {"id": "1", "date": "2023-01-01", "sample_count": 20, "value": 200},
        ]
        df = pd.DataFrame(data)
        
        result = resolve_duplicates(df)
        
        assert len(result) == 1
        assert result.iloc[0]["date"] == "2023-12-31"