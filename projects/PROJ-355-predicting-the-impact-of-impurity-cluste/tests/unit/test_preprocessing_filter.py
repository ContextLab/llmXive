import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.preprocessing import filter_zero_impurity_configs, generate_preprocessing_report

def test_filter_zero_impurity_with_species_column():
    """Test filtering when 'species' column indicates impurity presence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / 'input.csv'
        output_path = Path(tmpdir) / 'output.csv'
        
        # Create test data: some rows have species, some are empty
        data = {
            'species': ['Cr', 'Mo', '', None, 'W'],
            'rdf_peak': [1.0, 2.0, 3.0, 4.0, 5.0],
            'pair_corr': [0.1, 0.2, 0.3, 0.4, 0.5],
            'voronoi_count': [10, 11, 12, 13, 14]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        stats = filter_zero_impurity_configs(input_path, output_path)
        
        # Load result
        result_df = pd.read_csv(output_path)
        
        # Check counts
        assert stats['initial_count'] == 5
        assert stats['excluded_count'] == 2  # '' and None
        assert stats['filtered_count'] == 3
        
        # Check content
        assert len(result_df) == 3
        assert all(result_df['species'].notna())
        assert all(result_df['species'].astype(str).str.strip() != '')
        
        assert result_df['species'].tolist() == ['Cr', 'Mo', 'W']

def test_filter_zero_impurity_with_impurity_species_column():
    """Test filtering when 'impurity_species' column is used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / 'input.csv'
        output_path = Path(tmpdir) / 'output.csv'
        
        data = {
            'impurity_species': ['Fe', '', 'Ni'],
            'value': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        stats = filter_zero_impurity_configs(input_path, output_path)
        
        result_df = pd.read_csv(output_path)
        
        assert stats['excluded_count'] == 1
        assert len(result_df) == 2
        assert result_df['impurity_species'].tolist() == ['Fe', 'Ni']

def test_generate_preprocessing_report():
    """Test report generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / 'report.json'
        stats = {
            'initial_count': 10,
            'filtered_count': 8,
            'excluded_count': 2,
            'input_path': 'test.csv',
            'output_path': 'test_out.csv'
        }
        
        generate_preprocessing_report(stats, report_path)
        
        assert report_path.exists()
        with open(report_path, 'r') as f:
            loaded_stats = json.load(f)
        
        assert loaded_stats['excluded_count'] == 2
        assert loaded_stats['filtered_count'] == 8
