import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import extract_features, flag_undefined_imperative_ratio

class TestT015UndefinedRatios:
    """
    Tests for T015: Handle Undefined Ratios.
    Verifies that prompts with zero total sentences are flagged correctly.
    """

    def test_extract_features_normal_sentence(self):
        """Test feature extraction with normal text."""
        row = {
            'prompt_id': 'test-001',
            'prompt': 'This is a test sentence. It has two sentences. Please count them.'
        }
        features = extract_features(row)
        assert features['total_sentences'] >= 1
        assert features['is_ratio_undefined'] is False  # Should not be undefined
        assert features['ratio_safe_value'] == features['imperative_ratio']

    def test_extract_features_empty_text(self):
        """Test feature extraction with empty text (T015 trigger)."""
        row = {
            'prompt_id': 'test-empty',
            'prompt': ''
        }
        features = extract_features(row)
        assert features['total_sentences'] == 0
        assert features['imperative_ratio'] == 0.0  # Safe value
        assert features['citation_density'] == 0.0

    def test_flag_undefined_imperative_ratio_normal(self):
        """Test flagging logic for normal rows."""
        features_list = [
            {'prompt_id': '1', 'total_sentences': 5, 'imperative_ratio': 0.4},
            {'prompt_id': '2', 'total_sentences': 10, 'imperative_ratio': 0.2}
        ]
        result = flag_undefined_imperative_ratio(features_list)
        assert result[0]['is_ratio_undefined'] is False
        assert result[0]['ratio_safe_value'] == 0.4
        assert result[1]['is_ratio_undefined'] is False
        assert result[1]['ratio_safe_value'] == 0.2

    def test_flag_undefined_imperative_ratio_zero_sentences(self):
        """Test flagging logic for rows with zero sentences (T015 core)."""
        features_list = [
            {'prompt_id': '1', 'total_sentences': 0, 'imperative_ratio': 0.0},
            {'prompt_id': '2', 'total_sentences': 3, 'imperative_ratio': 0.3}
        ]
        result = flag_undefined_imperative_ratio(features_list)

        # First row should be flagged
        assert result[0]['is_ratio_undefined'] is True
        assert result[0]['ratio_safe_value'] == 0.0

        # Second row should not be flagged
        assert result[1]['is_ratio_undefined'] is False
        assert result[1]['ratio_safe_value'] == 0.3

    def test_feature_schema_contains_t015_columns(self):
        """Verify that the output schema includes T015 specific columns."""
        # Simulate a row that would be processed
        row = {'prompt_id': 'x', 'prompt': ''}
        feat = extract_features(row)
        feat_list = [feat]
        feat_list = flag_undefined_imperative_ratio(feat_list)

        assert 'is_ratio_undefined' in feat_list[0]
        assert 'ratio_safe_value' in feat_list[0]
        assert isinstance(feat_list[0]['is_ratio_undefined'], bool)
        assert isinstance(feat_list[0]['ratio_safe_value'], float)

    def test_integration_pipeline_with_empty_rows(self):
        """Integration test: Ensure pipeline handles empty rows without crashing."""
        # Create a temporary CSV with an empty row
        import tempfile
        import csv

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt_id', 'prompt'])
            writer.writeheader()
            writer.writerow({'prompt_id': '1', 'prompt': 'Normal sentence.'})
            writer.writerow({'prompt_id': '2', 'prompt': ''}) # Empty
            writer.writerow({'prompt_id': '3', 'prompt': 'Another sentence.'})
            temp_input = f.name

        try:
            temp_output = tempfile.mktemp(suffix='.csv')
            # Run the pipeline logic directly
            df = pd.read_csv(temp_input)
            features_list = []
            for _, row in df.iterrows():
                features_list.append(extract_features(row.to_dict()))
            features_list = flag_undefined_imperative_ratio(features_list)
            out_df = pd.DataFrame(features_list)
            out_df.to_csv(temp_output, index=False)

            # Verify output
            out_df_check = pd.read_csv(temp_output)
            assert len(out_df_check) == 3
            # Check the empty row
            empty_row = out_df_check[out_df_check['prompt_id'] == '2'].iloc[0]
            assert empty_row['is_ratio_undefined'] == True
            assert empty_row['ratio_safe_value'] == 0.0
        finally:
            os.unlink(temp_input)
            if os.path.exists(temp_output):
                os.unlink(temp_output)
