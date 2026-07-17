"""
Unit tests for T015: Imperative ratio validation logic.

These tests verify that the validation logic correctly identifies
prompts with undefined imperative ratios (zero total sentences).
"""
import pytest
import os
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from validation_logic import (
    flag_undefined_imperative_ratio,
    validate_features_for_imperative_ratio,
    run_t015_validation_pipeline
)


class TestFlagUndefinedImperativeRatio:
    """Tests for the flag_undefined_imperative_ratio function."""
    
    def test_flags_zero_sentence_prompts(self):
        """Test that prompts with zero total sentences are flagged."""
        features = [
            {'prompt_id': 'p1', 'total_sentences': 0, 'imperative_count': 0},
            {'prompt_id': 'p2', 'total_sentences': 5, 'imperative_count': 2},
            {'prompt_id': 'p3', 'total_sentences': 0, 'imperative_count': 0}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            total, flagged_count = flag_undefined_imperative_ratio(
                'dummy_input.csv', 
                temp_path, 
                features
            )
            
            assert total == 3
            assert flagged_count == 2
            
            # Verify the report file
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            flagged_ids = {row['prompt_id'] for row in rows}
            assert flagged_ids == {'p1', 'p3'}
        finally:
            os.unlink(temp_path)
    
    def test_no_flags_when_all_have_sentences(self):
        """Test that no prompts are flagged when all have non-zero sentences."""
        features = [
            {'prompt_id': 'p1', 'total_sentences': 1, 'imperative_count': 0},
            {'prompt_id': 'p2', 'total_sentences': 5, 'imperative_count': 2},
            {'prompt_id': 'p3', 'total_sentences': 3, 'imperative_count': 1}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            total, flagged_count = flag_undefined_imperative_ratio(
                'dummy_input.csv', 
                temp_path, 
                features
            )
            
            assert total == 3
            assert flagged_count == 0
            
            # Verify the report file is empty (header only)
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 0
        finally:
            os.unlink(temp_path)
    
    def test_handles_empty_features_list(self):
        """Test that empty features list is handled gracefully."""
        features = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            total, flagged_count = flag_undefined_imperative_ratio(
                'dummy_input.csv', 
                temp_path, 
                features
            )
            
            assert total == 0
            assert flagged_count == 0
        finally:
            os.unlink(temp_path)


class TestValidateFeaturesForImperativeRatio:
    """Tests for the validate_features_for_imperative_ratio function."""
    
    def test_adds_validation_flag_to_features(self):
        """Test that validation flags are correctly added to features."""
        # Create a mock input CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt_id', 'text', 'label'])
            writer.writeheader()
            writer.writerow({'prompt_id': 'p1', 'text': 'Test text.', 'label': 'test'})
            writer.writerow({'prompt_id': 'p2', 'text': 'Another test.', 'label': 'test'})
            input_path = f.name
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'output.csv')
            report_path = os.path.join(tmpdir, 'report.csv')
            
            # Mock run_feature_extraction to return predictable data
            mock_features = [
                {'prompt_id': 'p1', 'total_sentences': 0, 'imperative_count': 0, 'text': 'Test text.'},
                {'prompt_id': 'p2', 'total_sentences': 1, 'imperative_count': 1, 'text': 'Another test.'}
            ]
            
            with patch('validation_logic.run_feature_extraction', return_value=mock_features):
                success = validate_features_for_imperative_ratio(
                    input_path, 
                    output_path, 
                    report_path
                )
                
                assert success is True
                
                # Verify output file has the validation flag
                with open(output_path, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                assert len(rows) == 2
                
                # Check that imperative_ratio_undefined flag is set correctly
                p1_row = next(r for r in rows if r['prompt_id'] == 'p1')
                p2_row = next(r for r in rows if r['prompt_id'] == 'p2')
                
                assert p1_row['imperative_ratio_undefined'] == 'True'
                assert p2_row['imperative_ratio_undefined'] == 'False'
        
        os.unlink(input_path)
    
    def test_returns_false_when_no_features_extracted(self):
        """Test that function returns False when no features are extracted."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt_id', 'text', 'label'])
            writer.writeheader()
            writer.writerow({'prompt_id': 'p1', 'text': 'Test text.', 'label': 'test'})
            input_path = f.name
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'output.csv')
            report_path = os.path.join(tmpdir, 'report.csv')
            
            with patch('validation_logic.run_feature_extraction', return_value=[]):
                success = validate_features_for_imperative_ratio(
                    input_path, 
                    output_path, 
                    report_path
                )
                
                assert success is False
        
        os.unlink(input_path)


class TestRunT015ValidationPipeline:
    """Tests for the main pipeline entry point."""
    
    def test_fails_when_input_not_found(self):
        """Test that pipeline fails when input file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            success = run_t015_validation_pipeline()
            assert success is False
    
    def test_succeeds_when_input_exists_and_features_valid(self):
        """Test that pipeline succeeds with valid input and features."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt_id', 'text', 'label'])
            writer.writeheader()
            writer.writerow({'prompt_id': 'p1', 'text': 'Test text.', 'label': 'test'})
            input_path = f.name
        
        try:
            with patch('os.path.exists', return_value=True):
                mock_features = [
                    {'prompt_id': 'p1', 'total_sentences': 1, 'imperative_count': 1, 'text': 'Test text.'}
                ]
                
                with patch('validation_logic.run_feature_extraction', return_value=mock_features):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        # Override paths to use temp directory
                        with patch('validation_logic.validate_features_for_imperative_ratio', return_value=True):
                            success = run_t015_validation_pipeline()
                            assert success is True
        finally:
            os.unlink(input_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])