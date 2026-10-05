"""
Unit tests for T014: Filter Records
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from t014_filter_records import filter_records

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'participant_id': ['p001', 'p002', 'p003', 'p004', 'p005'],
        'label': ['AD', None, 'Control', 'MCI', 'AD'],
        'text': [
            'This is a long text with more than fifty words. ' * 2,
            'Short text.',
            'Another long text with more than fifty words. ' * 2,
            'Just enough words here to pass the filter. ' * 2,
            'Short again.'
        ]
    })

def test_filter_records_missing_label(sample_df):
    """Test filtering of records with missing labels."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / 'input.csv'
        output_path = Path(tmpdir) / 'output.csv'
        exclusions_path = Path(tmpdir) / 'exclusions.log'
        
        sample_df.to_csv(input_path, index=False)
        
        filtered_count, excluded_count = filter_records(
            input_path, output_path, exclusions_path
        )
        
        # p002 has missing label, p005 has too short text
        assert excluded_count == 2
        assert filtered_count == 3
        
        # Verify exclusions log
        with open(exclusions_path, 'r') as f:
            exclusions = [json.loads(line) for line in f]
        
        reason_codes = [e['reason'] for e in exclusions]
        assert 'MISSING_LABEL' in reason_codes
        assert 'TOO_SHORT' in reason_codes

def test_filter_records_too_short(sample_df):
    """Test filtering of records with text < 50 words."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / 'input.csv'
        output_path = Path(tmpdir) / 'output.csv'
        exclusions_path = Path(tmpdir) / 'exclusions.log'
        
        sample_df.to_csv(input_path, index=False)
        
        filtered_count, excluded_count = filter_records(
            input_path, output_path, exclusions_path
        )
        
        # p002 (missing label) and p005 (too short) should be excluded
        assert excluded_count == 2
        
        # Verify output contains only valid records
        output_df = pd.read_csv(output_path)
        assert len(output_df) == 3
        assert output_df['label'].notnull().all()
        
        for _, row in output_df.iterrows():
            assert len(str(row['text']).split()) >= 50
