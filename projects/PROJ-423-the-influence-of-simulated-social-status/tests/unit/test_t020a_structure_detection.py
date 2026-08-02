import os
import json
import tempfile
import pandas as pd
import pytest
from preprocess import detect_data_structure, load_raw_data, save_processed_data

class TestT020aStructureDetection:
    """
    Tests for Task T020a: Dynamic generation of structure_config.json.
    Verifies that the logic correctly identifies between-subjects vs within-subjects
    designs based on unique participant_id counts vs total rows.
    """

    def test_detect_between_subjects_structure(self, tmp_path):
        """
        Verify that a dataset where unique participant_ids == total rows
        is correctly identified as 'between-subjects'.
        """
        # Create a between-subjects dataframe (1 row per participant)
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'status_level': ['High', 'High', 'Low', 'Low'],
            'observed_behavior': ['Risky', 'Conservative', 'Risky', 'Conservative'],
            'risk_taking_score': [0.8, 0.3, 0.6, 0.2]
        }
        df = pd.DataFrame(data)
        
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        config_path = output_dir / "structure_config.json"
        
        # Run detection
        result = detect_data_structure(df, str(config_path))
        
        # Assertions
        assert result['type'] == 'between-subjects'
        assert result['n_subjects'] == 4
        assert result['model_type'] == 'fixed-effects'
        
        # Verify file was written correctly
        assert config_path.exists()
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        assert saved_config == result

    def test_detect_within_subjects_structure(self, tmp_path):
        """
        Verify that a dataset where unique participant_ids < total rows
        is correctly identified as 'within-subjects'.
        """
        # Create a within-subjects dataframe (multiple rows per participant)
        # P1 appears twice, P2 appears twice
        data = {
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'status_level': ['High', 'Low', 'High', 'Low'],
            'observed_behavior': ['Risky', 'Risky', 'Conservative', 'Conservative'],
            'risk_taking_score': [0.8, 0.5, 0.3, 0.2]
        }
        df = pd.DataFrame(data)
        
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        config_path = output_dir / "structure_config.json"
        
        # Run detection
        result = detect_data_structure(df, str(config_path))
        
        # Assertions
        assert result['type'] == 'within-subjects'
        assert result['n_subjects'] == 2
        assert result['model_type'] == 'mixed-effects'
        
        # Verify file was written correctly
        assert config_path.exists()
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        assert saved_config == result

    def test_missing_participant_id_column(self, tmp_path):
        """
        Verify that a ValueError is raised if 'participant_id' is missing.
        """
        data = {
            'subject': ['A', 'B'],
            'value': [1, 2]
        }
        df = pd.DataFrame(data)
        
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        config_path = output_dir / "structure_config.json"
        
        with pytest.raises(ValueError, match="Input dataframe must contain 'participant_id' column."):
            detect_data_structure(df, str(config_path))

    def test_end_to_end_pipeline_integration(self, tmp_path):
        """
        Integration test: Run a mock pipeline that creates a CSV,
        then detects structure, ensuring the file exists and is valid.
        """
        # 1. Create raw input CSV (within-subjects)
        input_path = tmp_path / "raw" / "data.csv"
        input_path.parent.mkdir()
        raw_data = {
            'participant_id': ['S1', 'S1', 'S2', 'S2'],
            'status_level': ['High', 'Low', 'High', 'Low'],
            'observed_behavior': ['Risky', 'Risky', 'Conservative', 'Conservative'],
            'risk_taking_score': [0.9, 0.4, 0.2, 0.1]
        }
        pd.DataFrame(raw_data).to_csv(input_path, index=False)
        
        # 2. Define output paths
        processed_path = tmp_path / "processed" / "cleaned_data.csv"
        structure_path = tmp_path / "processed" / "structure_config.json"
        
        # 3. Run pipeline components manually to simulate main() flow
        from preprocess import load_raw_data, map_to_categorical, handle_missing_values, save_processed_data
        
        df = load_raw_data(str(input_path))
        df = map_to_categorical(df)
        df = handle_missing_values(df, 'exclude')
        save_processed_data(df, str(processed_path))
        
        # 4. Detect structure (The T020a requirement)
        result = detect_data_structure(df, str(structure_path))
        
        # 5. Verify
        assert result['type'] == 'within-subjects'
        assert structure_path.exists()
        
        with open(structure_path, 'r') as f:
            config = json.load(f)
        
        assert config['n_subjects'] == 2
        assert config['model_type'] == 'mixed-effects'