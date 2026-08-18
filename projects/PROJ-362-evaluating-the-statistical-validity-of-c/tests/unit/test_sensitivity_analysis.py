"""
Unit tests for sensitivity analysis module (T024).

Tests:
- determine_significance logic
- load_corrected_p_values with mock data
- run_sensitivity_analysis output structure
"""
import os
import csv
import tempfile
import pytest
from sensitivity_analysis import determine_significance, load_corrected_p_values, run_sensitivity_analysis

class TestDetermineSignificance:
    def test_significant_when_p_less_than_alpha(self):
        assert determine_significance(0.04, 0.05) is True
    
    def test_significant_when_p_equal_to_alpha(self):
        assert determine_significance(0.05, 0.05) is True
    
    def test_not_significant_when_p_greater_than_alpha(self):
        assert determine_significance(0.06, 0.05) is False

class TestLoadCorrectedPValues:
    def test_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
            writer.writeheader()
            writer.writerow({
                'query_id': 1,
                'metric': 'NDCG@10',
                'raw_p': 0.03,
                'corrected_p': 0.045,
                'is_significant': 'True'
            })
            writer.writerow({
                'query_id': 2,
                'metric': 'MAP',
                'raw_p': 0.08,
                'corrected_p': 0.09,
                'is_significant': 'False'
            })
            temp_path = f.name
        
        try:
            data = load_corrected_p_values(temp_path)
            assert len(data) == 2
            assert data[0]['query_id'] == 1
            assert data[0]['corrected_p'] == 0.045
            assert data[0]['is_significant'] is True
            assert data[1]['query_id'] == 2
            assert data[1]['is_significant'] is False
        finally:
            os.unlink(temp_path)
    
    def test_load_empty_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
            writer.writeheader()
            temp_path = f.name
        
        try:
            data = load_corrected_p_values(temp_path)
            assert len(data) == 0
        finally:
            os.unlink(temp_path)

class TestRunSensitivityAnalysis:
    def test_sensitivity_analysis_output_structure(self):
        # Create a temporary CSV with known data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
            writer.writeheader()
            # 3 queries: 
            # q1: p=0.04 -> significant at 0.05 and 0.10
            # q2: p=0.06 -> significant only at 0.10
            # q3: p=0.12 -> not significant at any
            writer.writerow({'query_id': 1, 'metric': 'NDCG@10', 'raw_p': 0.03, 'corrected_p': 0.04, 'is_significant': 'True'})
            writer.writerow({'query_id': 2, 'metric': 'MAP', 'raw_p': 0.05, 'corrected_p': 0.06, 'is_significant': 'False'})
            writer.writerow({'query_id': 3, 'metric': 'NDCG@10', 'raw_p': 0.11, 'corrected_p': 0.12, 'is_significant': 'False'})
            input_path = f.name
        
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_path = f.name
        
        try:
            alphas = [0.05, 0.10]
            results = run_sensitivity_analysis(
                alphas=alphas,
                input_file=input_path,
                output_file=output_path
            )
            
            # Check results structure
            assert len(results) == 2
            assert results[0]['alpha'] == 0.05
            assert results[0]['significant_count'] == 1  # Only q1
            assert results[1]['alpha'] == 0.10
            assert results[1]['significant_count'] == 2  # q1 and q2
            
            # Check output file exists and has correct content
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['alpha'] == '0.05'
                assert rows[0]['significant_count'] == '1'
                assert rows[1]['alpha'] == '0.10'
                assert rows[1]['significant_count'] == '2'
        finally:
            os.unlink(input_path)
            os.unlink(output_path)