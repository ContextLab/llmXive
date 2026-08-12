import pandas as pd
import numpy as np
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from code.data_collection import validate_and_clean_responses, aggregate_reader_scores, run_aggregation_pipeline

class TestDataCollection:

    def test_validate_and_clean_responses_missing_columns(self):
        """Test that missing required columns raise an error."""
        data = {'story_id': [1], 'empathy_score': [50]} # Missing moral_judgement_score and participant_id
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_and_clean_responses(df)

    def test_validate_and_clean_responses_drops_missing_scores(self):
        """Test that rows with missing scores are dropped."""
        data = {
            'story_id': [1, 2, 3],
            'empathy_score': [50.0, np.nan, 60.0],
            'moral_judgement_score': [70.0, 75.0, np.nan],
            'participant_id': ['p1', 'p2', 'p3']
        }
        df = pd.DataFrame(data)
        
        cleaned = validate_and_clean_responses(df)
        
        assert len(cleaned) == 1
        assert cleaned.iloc[0]['story_id'] == 1

    def test_aggregate_reader_scores_basic(self):
        """Test basic aggregation of reader scores."""
        stories = [
            {'story_id': 's1', 'narrator_distance_score': 0.8},
            {'story_id': 's2', 'narrator_distance_score': 0.2}
        ]
        
        responses = pd.DataFrame({
            'story_id': ['s1', 's1', 's2'],
            'empathy_score': [50.0, 60.0, 40.0],
            'moral_judgement_score': [70.0, 80.0, 60.0],
            'participant_id': ['p1', 'p2', 'p3']
        })
        
        result = aggregate_reader_scores(stories, responses)
        
        assert len(result) == 2
        assert 'perspective_score' in result.columns
        assert 'empathy_score' in result.columns
        assert 'moral_judgement_score' in result.columns
        
        # Check means
        s1_row = result[result['story_id'] == 's1'].iloc[0]
        assert s1_row['perspective_score'] == 0.8
        assert s1_row['empathy_score'] == 55.0 # (50+60)/2
        assert s1_row['moral_judgement_score'] == 75.0 # (70+80)/2

    def test_aggregate_reader_scores_no_match(self):
        """Test aggregation when no story_ids match."""
        stories = [
            {'story_id': 's1', 'narrator_distance_score': 0.8}
        ]
        responses = pd.DataFrame({
            'story_id': ['s2', 's3'],
            'empathy_score': [50.0, 60.0],
            'moral_judgement_score': [70.0, 80.0],
            'participant_id': ['p1', 'p2']
        })
        
        result = aggregate_reader_scores(stories, responses)
        assert result.empty

    def test_run_aggregation_pipeline_integration(self):
        """Test the full pipeline function writing to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            features_path = os.path.join(tmpdir, 'features.json')
            responses_path = os.path.join(tmpdir, 'responses.csv')
            output_path = os.path.join(tmpdir, 'aligned.csv')
            
            # Create features
            stories = [
                {'story_id': 's1', 'narrator_distance_score': 0.9},
                {'story_id': 's2', 'narrator_distance_score': 0.1}
            ]
            with open(features_path, 'w') as f:
                json.dump(stories, f)
            
            # Create responses
            responses = pd.DataFrame({
                'story_id': ['s1', 's1', 's2'],
                'empathy_score': [80.0, 90.0, 30.0],
                'moral_judgement_score': [85.0, 95.0, 35.0],
                'participant_id': ['p1', 'p2', 'p3']
            })
            responses.to_csv(responses_path, index=False)
            
            # Run pipeline
            result = run_aggregation_pipeline(features_path, responses_path, output_path)
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify content
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 2
            assert list(loaded_df.columns) == ['story_id', 'perspective_score', 'empathy_score', 'moral_judgement_score']
            
            # Verify values
            s1 = loaded_df[loaded_df['story_id'] == 's1'].iloc[0]
            assert s1['perspective_score'] == 0.9
            assert s1['empathy_score'] == 85.0
            assert s1['moral_judgement_score'] == 90.0