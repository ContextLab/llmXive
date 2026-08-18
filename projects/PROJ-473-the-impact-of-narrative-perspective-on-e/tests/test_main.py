import pytest
import json
import os
import tempfile
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / 'code'
import sys
sys.path.insert(0, str(code_dir))

from main import run_matching_step
from config import get_config

def test_matching_step_creates_output():
    """Test that run_matching_step creates the output file."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        features_path = os.path.join(tmpdir, 'features.json')
        target_path = os.path.join(tmpdir, 'target.csv')
        output_path = os.path.join(tmpdir, 'results.json')
        
        # Create dummy features
        features = [{'story_id': 'test1', 'raw_text': 'This is a test story.', 'narrator_distance_score': 0.5}]
        with open(features_path, 'w') as f:
            json.dump(features, f)
        
        # Create dummy target
        with open(target_path, 'w') as f:
            f.write('story_id,moral_judgement_score,text_description\n')
            f.write('test1,0.8,This is a test story.\n')
        
        # Run matching step
        run_matching_step(
            type('Args', (), {'input': features_path, 'target': target_path, 'output': output_path})()
        )
        
        # Verify output exists
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        assert isinstance(results, list)
        if results:
            assert 'story_id' in results[0]
            assert 'match_id' in results[0]
            assert 'similarity_score' in results[0]
            assert 'rank' in results[0]

def test_matching_step_with_threshold():
    """Test that matching respects the threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        features_path = os.path.join(tmpdir, 'features.json')
        target_path = os.path.join(tmpdir, 'target.csv')
        output_path = os.path.join(tmpdir, 'results.json')
        
        # Create features with known scores
        features = [
            {'story_id': 'test1', 'raw_text': 'I went to the store.', 'narrator_distance_score': 1.0},
            {'story_id': 'test2', 'raw_text': 'He went to the store.', 'narrator_distance_score': 0.0}
        ]
        with open(features_path, 'w') as f:
            json.dump(features, f)
        
        # Create target
        with open(target_path, 'w') as f:
            f.write('story_id,moral_judgement_score,text_description\n')
            f.write('target1,0.5,I went to the store.\n')
            f.write('target2,0.3,He went to the store.\n')
        
        # Run matching
        run_matching_step(
            type('Args', (), {'input': features_path, 'target': target_path, 'output': output_path})()
        )
        
        # Verify output
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        # Check that results are within threshold (0.30 by default)
        for r in results:
            assert r['similarity_score'] >= 0.30, f"Score {r['similarity_score']} below threshold"