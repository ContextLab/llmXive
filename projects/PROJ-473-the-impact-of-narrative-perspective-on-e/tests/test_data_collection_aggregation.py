import pytest
import pandas as pd
import json
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection import aggregate_reader_scores, run_aggregation_pipeline

def test_aggregate_reader_scores_basic():
    """Test basic aggregation logic with valid data."""
    # Mock stories data (from perspective_features.json)
    stories = [
        {'story_id': 's1', 'narrator_distance_score': 0.9, 'raw_text': 'I walked...'},
        {'story_id': 's2', 'narrator_distance_score': 0.1, 'raw_text': 'He walked...'},
    ]
    
    # Mock responses data
    responses = pd.DataFrame({
        'story_id': ['s1', 's1', 's2'],
        'empathy_score': [80.0, 82.0, 40.0],
        'moral_judgement_score': [75.0, 77.0, 35.0],
        'participant_id': ['p1', 'p2', 'p1']
    })
    
    result = aggregate_reader_scores(stories, responses)
    
    assert len(result) == 2
    assert set(result.columns) == {'story_id', 'perspective_score', 'empathy_score', 'moral_judgement_score'}
    
    # Check s1 aggregation (mean of 80 and 82)
    s1_row = result[result['story_id'] == 's1'].iloc[0]
    assert s1_row['perspective_score'] == 0.9
    assert abs(s1_row['empathy_score'] - 81.0) < 0.01
    assert abs(s1_row['moral_judgement_score'] - 76.0) < 0.01
    
    # Check s2 aggregation
    s2_row = result[result['story_id'] == 's2'].iloc[0]
    assert s2_row['perspective_score'] == 0.1
    assert abs(s2_row['empathy_score'] - 40.0) < 0.01
    assert abs(s2_row['moral_judgement_score'] - 35.0) < 0.01

def test_aggregate_reader_scores_empty_responses():
    """Test behavior when no matching story IDs are found."""
    stories = [
        {'story_id': 's1', 'narrator_distance_score': 0.9},
    ]
    
    responses = pd.DataFrame({
        'story_id': ['s2', 's3'],
        'empathy_score': [50.0, 60.0],
        'moral_judgement_score': [55.0, 65.0],
        'participant_id': ['p1', 'p2']
    })
    
    result = aggregate_reader_scores(stories, responses)
    
    assert result.empty

def test_aggregate_reader_scores_missing_columns():
    """Test error handling for missing required columns."""
    stories = [
        {'story_id': 's1'}, # Missing narrator_distance_score
    ]
    
    responses = pd.DataFrame({
        'story_id': ['s1'],
        'empathy_score': [50.0],
        'moral_judgement_score': [55.0],
        'participant_id': ['p1']
    })
    
    with pytest.raises(ValueError, match="Stories data missing required columns"):
        aggregate_reader_scores(stories, responses)

def test_run_aggregation_pipeline(tmp_path):
    """Test the full pipeline writing to a file."""
    # Create temp input files
    stories_data = [
        {'story_id': 's1', 'narrator_distance_score': 0.8, 'raw_text': 'I walked...'},
    ]
    features_file = tmp_path / "features.json"
    with open(features_file, 'w') as f:
        json.dump(stories_data, f)
    
    responses_data = pd.DataFrame({
        'story_id': ['s1', 's1'],
        'empathy_score': [90.0, 92.0],
        'moral_judgement_score': [85.0, 87.0],
        'participant_id': ['p1', 'p2']
    })
    responses_file = tmp_path / "responses.csv"
    responses_data.to_csv(responses_file, index=False)
    
    output_file = tmp_path / "aligned.csv"
    
    result_df = run_aggregation_pipeline(
        str(features_file), 
        str(responses_file), 
        str(output_file)
    )
    
    assert os.path.exists(output_file)
    assert len(result_df) == 1
    assert list(result_df.columns) == ['story_id', 'perspective_score', 'empathy_score', 'moral_judgement_score']
    assert result_df['story_id'].iloc[0] == 's1'
    assert abs(result_df['empathy_score'].iloc[0] - 91.0) < 0.01