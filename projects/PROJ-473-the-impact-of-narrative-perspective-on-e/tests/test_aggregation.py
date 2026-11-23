import pandas as pd
import json
import os
import tempfile
from code.data_collection import validate_and_clean_responses, aggregate_reader_scores, run_aggregation_pipeline

def test_validate_and_clean_responses():
    """Test validation and cleaning of reader responses."""
    # Create sample data
    data = {
        'story_id': ['s1', 's2', 's3', 's4'],
        'empathy_score': [3.5, 4.0, None, 2.5],
        'moral_judgement_score': [4.0, 3.0, 2.5, None],
        'participant_id': ['p1', 'p2', 'p3', 'p4']
    }
    df = pd.DataFrame(data)
    
    cleaned = validate_and_clean_responses(df)
    
    # Should have removed rows with NaN scores
    assert len(cleaned) == 2
    assert 's3' not in cleaned['story_id'].values
    assert 's4' not in cleaned['story_id'].values

def test_aggregate_reader_scores():
    """Test aggregation of scores per story."""
    stories = [
        {'story_id': 's1', 'narrator_distance_score': 0.9},
        {'story_id': 's2', 'narrator_distance_score': 0.1},
        {'story_id': 's3', 'narrator_distance_score': 0.5}
    ]
    
    responses = pd.DataFrame({
        'story_id': ['s1', 's1', 's2', 's3', 's3', 's3'],
        'empathy_score': [4.0, 4.2, 2.0, 3.0, 3.2, 2.8],
        'moral_judgement_score': [5.0, 4.8, 2.0, 3.0, 3.2, 2.8],
        'participant_id': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6']
    })
    
    result = aggregate_reader_scores(stories, responses)
    
    # Should have 3 rows (s1, s2, s3)
    assert len(result) == 3
    assert 'story_id' in result.columns
    assert 'perspective_score' in result.columns
    assert 'empathy_score' in result.columns
    assert 'moral_judgement_score' in result.columns
    
    # Check aggregation (mean)
    s1_row = result[result['story_id'] == 's1'].iloc[0]
    assert abs(s1_row['empathy_score'] - 4.1) < 0.01
    assert abs(s1_row['moral_judgement_score'] - 4.9) < 0.01

def test_run_aggregation_pipeline():
    """Test full aggregation pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        features_path = os.path.join(tmpdir, 'features.json')
        responses_path = os.path.join(tmpdir, 'responses.csv')
        output_path = os.path.join(tmpdir, 'aligned.csv')
        
        # Create features
        features = [
            {'story_id': 's1', 'narrator_distance_score': 0.9},
            {'story_id': 's2', 'narrator_distance_score': 0.1}
        ]
        with open(features_path, 'w') as f:
            json.dump(features, f)
        
        # Create responses
        responses = pd.DataFrame({
            'story_id': ['s1', 's2'],
            'empathy_score': [4.0, 2.0],
            'moral_judgement_score': [5.0, 2.0],
            'participant_id': ['p1', 'p2']
        })
        responses.to_csv(responses_path, index=False)
        
        # Run pipeline
        result = run_aggregation_pipeline(features_path, responses_path, output_path)
        
        # Check output exists
        assert os.path.exists(output_path)
        
        # Check columns
        df = pd.read_csv(output_path)
        assert list(df.columns) == ['story_id', 'perspective_score', 'empathy_score', 'moral_judgement_score']
        assert len(df) == 2