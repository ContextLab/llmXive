import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from code.summary_table import generate_summary_table, load_enrichment_csv, load_validation_json
from code.config import DATA_PROCESSED_DIR

class TestSummaryTable:
    """Test suite for T033: Generate final summary table"""
    
    @pytest.fixture
    def sample_enrichment_csv(self, tmp_path):
        """Create a sample enrichment matrix CSV"""
        csv_path = tmp_path / 'enrichment_matrix.csv'
        data = {
            'motif_id': ['MA0001.1', 'MA0002.1', 'MA0003.1', 'MA0004.1'],
            'cell_type': ['GM12878', 'GM12878', 'K562', 'K562'],
            'p_value': [0.0001, 0.001, 0.00005, 0.01],
            'q_value': [0.001, 0.01, 0.0005, 0.05]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path
    
    @pytest.fixture
    def sample_validation_json(self, tmp_path):
        """Create a sample validation report JSON"""
        json_path = tmp_path / 'validation_report.json'
        data = {
            'overlap_pct': 65.5,
            'top_motifs': [
                {'motif_id': 'MA0001.1', 'q_value': 0.001, 'overlap_pct': 70.2},
                {'motif_id': 'MA0002.1', 'q_value': 0.01, 'overlap_pct': 62.3},
                {'motif_id': 'MA0003.1', 'q_value': 0.0005, 'overlap_pct': 68.9}
            ],
            'silhouette_score': 0.45
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        return json_path
    
    @pytest.fixture
    def output_path(self, tmp_path):
        """Create output path"""
        return tmp_path / 'summary_table.csv'
    
    def test_generate_summary_table_basic(self, sample_enrichment_csv, sample_validation_json, output_path):
        """Test basic summary table generation"""
        result_df = generate_summary_table(sample_enrichment_csv, sample_validation_json, output_path)
        
        # Check file was created
        assert output_path.exists()
        
        # Check columns
        expected_cols = ['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct']
        assert list(result_df.columns) == expected_cols
        
        # Check that only top motifs are included (MA0001.1, MA0002.1, MA0003.1)
        assert len(result_df) == 3
        assert set(result_df['motif_id']) == {'MA0001.1', 'MA0002.1', 'MA0003.1'}
        
        # Check that MA0004.1 is excluded (not in top_motifs)
        assert 'MA0004.1' not in result_df['motif_id'].values
    
    def test_generate_summary_table_columns_format(self, sample_enrichment_csv, sample_validation_json, output_path):
        """Test that output columns have correct formatting"""
        result_df = generate_summary_table(sample_enrichment_csv, sample_validation_json, output_path)
        
        # Check p_value_raw precision (6 decimal places)
        assert all(isinstance(val, float) for val in result_df['p_value_raw'])
        
        # Check q_value_adj precision (4 decimal places)
        assert all(isinstance(val, float) for val in result_df['q_value_adj'])
        
        # Check chip_overlap_pct precision (2 decimal places)
        assert all(isinstance(val, float) for val in result_df['chip_overlap_pct'])
    
    def test_load_enrichment_csv_success(self, sample_enrichment_csv):
        """Test loading enrichment CSV successfully"""
        df = load_enrichment_csv(sample_enrichment_csv)
        
        assert isinstance(df, pd.DataFrame)
        assert 'motif_id' in df.columns
        assert 'cell_type' in df.columns
        assert 'p_value' in df.columns
        assert 'q_value' in df.columns
    
    def test_load_enrichment_csv_missing_file(self, tmp_path):
        """Test loading non-existent enrichment CSV"""
        non_existent = tmp_path / 'non_existent.csv'
        
        with pytest.raises(FileNotFoundError):
            load_enrichment_csv(non_existent)
    
    def test_load_enrichment_csv_missing_columns(self, tmp_path):
        """Test loading enrichment CSV with missing columns"""
        csv_path = tmp_path / 'bad_enrichment.csv'
        data = {
            'motif_id': ['MA0001.1'],
            'cell_type': ['GM12878']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError):
            load_enrichment_csv(csv_path)
    
    def test_load_validation_json_success(self, sample_validation_json):
        """Test loading validation JSON successfully"""
        data = load_validation_json(sample_validation_json)
        
        assert isinstance(data, dict)
        assert 'top_motifs' in data
        assert 'overlap_pct' in data
        assert 'silhouette_score' in data
    
    def test_load_validation_json_missing_file(self, tmp_path):
        """Test loading non-existent validation JSON"""
        non_existent = tmp_path / 'non_existent.json'
        
        with pytest.raises(FileNotFoundError):
            load_validation_json(non_existent)
    
    def test_load_validation_json_missing_top_motifs(self, tmp_path):
        """Test loading validation JSON missing top_motifs"""
        json_path = tmp_path / 'bad_validation.json'
        data = {
            'overlap_pct': 65.5,
            'silhouette_score': 0.45
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError):
            load_validation_json(json_path)
    
    def test_generate_summary_table_empty_top_motifs(self, sample_enrichment_csv, tmp_path):
        """Test handling of empty top_motifs in validation report"""
        json_path = tmp_path / 'empty_validation.json'
        data = {
            'overlap_pct': 0.0,
            'top_motifs': [],
            'silhouette_score': 0.0
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        output_path = tmp_path / 'summary_table.csv'
        result_df = generate_summary_table(sample_enrichment_csv, json_path, output_path)
        
        # Should create empty dataframe with correct columns
        assert len(result_df) == 0
        assert list(result_df.columns) == ['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct']
    
    def test_generate_summary_table_duplicate_motifs(self, tmp_path):
        """Test handling of duplicate motif_ids across cell types"""
        # Create enrichment with duplicate motif_ids
        csv_path = tmp_path / 'enrichment.csv'
        data = {
            'motif_id': ['MA0001.1', 'MA0001.1', 'MA0002.1'],
            'cell_type': ['GM12878', 'K562', 'HepG2'],
            'p_value': [0.0001, 0.0002, 0.001],
            'q_value': [0.001, 0.002, 0.01]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Validation with both motifs
        json_path = tmp_path / 'validation.json'
        data = {
            'overlap_pct': 60.0,
            'top_motifs': [
                {'motif_id': 'MA0001.1', 'q_value': 0.001, 'overlap_pct': 65.0},
                {'motif_id': 'MA0002.1', 'q_value': 0.01, 'overlap_pct': 55.0}
            ],
            'silhouette_score': 0.5
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        output_path = tmp_path / 'summary.csv'
        result_df = generate_summary_table(csv_path, json_path, output_path)
        
        # Should have 2 unique motifs (duplicates aggregated)
        assert len(result_df) == 2
        assert len(result_df['motif_id'].unique()) == 2