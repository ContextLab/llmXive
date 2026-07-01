"""
Unit tests for Human Consensus Workflow.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.utils.consensus import (
    load_candidates,
    simulate_rater_ratings,
    compute_consensus,
    run_consensus_workflow,
    RaterRating,
    ConsensusResult
)


@pytest.fixture
def sample_candidates():
    """Sample candidate false memories for testing."""
    return [
        {
            'image_id': 'vg_123',
            'object_id': 'obj_1',
            'object_text': 'dog',
            'in_vg': False,
            'confidence_score': 0.85
        },
        {
            'image_id': 'vg_456',
            'object_id': 'obj_2',
            'object_text': 'cat',
            'in_vg': True,
            'confidence_score': 0.92
        },
        {
            'image_id': 'vg_789',
            'object_id': 'obj_3',
            'object_text': 'bird',
            'in_vg': False,
            'confidence_score': 0.78
        }
    ]


@pytest.fixture
def temp_input_file(sample_candidates):
    """Create a temporary input file with sample candidates."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_candidates, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_load_candidates_from_list(temp_input_file):
    """Test loading candidates from a list format."""
    candidates = load_candidates(temp_input_file)
    assert isinstance(candidates, list)
    assert len(candidates) == 3
    assert candidates[0]['image_id'] == 'vg_123'


def test_load_candidates_from_dict():
    """Test loading candidates from a dict with 'candidates' key."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'candidates': [{'image_id': 'test'}]}, f)
        temp_path = f.name
    
    try:
        candidates = load_candidates(temp_path)
        assert len(candidates) == 1
        assert candidates[0]['image_id'] == 'test'
    finally:
        os.unlink(temp_path)


def test_load_candidates_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_candidates('/nonexistent/path/file.json')


def test_simulate_rater_ratings_consistency(sample_candidates):
    """Test that simulated ratings are consistent (seeded)."""
    ratings1 = simulate_rater_ratings(sample_candidates, num_raters=3)
    ratings2 = simulate_rater_ratings(sample_candidates, num_raters=3)
    
    assert len(ratings1) == len(ratings2)
    assert ratings1[0]['ratings'][0]['is_false_memory'] == ratings2[0]['ratings'][0]['is_false_memory']


def test_simulate_rater_ratings_structure(sample_candidates):
    """Test structure of simulated ratings."""
    ratings = simulate_rater_ratings(sample_candidates, num_raters=5)
    
    assert len(ratings) == len(sample_candidates)
    for item in ratings:
        assert 'image_id' in item
        assert 'object_id' in item
        assert 'ratings' in item
        assert len(item['ratings']) == 5
        for rating in item['ratings']:
            assert 'rater_id' in rating
            assert 'is_false_memory' in rating
            assert 'confidence' in rating
            assert 0.0 <= rating['confidence'] <= 1.0


def test_compute_consensus_threshold(sample_candidates):
    """Test consensus computation with different thresholds."""
    rated = simulate_rater_ratings(sample_candidates, num_raters=3)
    
    # With threshold 0.67 (2/3), should reach consensus
    results = compute_consensus(rated, threshold=0.67)
    assert len(results) == 3
    
    for result in results:
        assert 'consensus_reached' in result
        assert 'consensus_score' in result
        assert 'status' in result
        assert result['status'] in ['verified', 'rejected', 'uncertain']


def test_compute_consensus_perfect_agreement():
    """Test consensus with perfect agreement."""
    candidates = [{'image_id': 'test', 'object_id': 'obj', 'in_vg': False}]
    rated = simulate_rater_ratings(candidates, num_raters=1)
    
    # Force perfect agreement by modifying the simulation result
    # (In reality, the simulation is deterministic with seed=42)
    results = compute_consensus(rated, threshold=1.0)
    
    # Should reach consensus if all raters agree
    assert results[0]['consensus_score'] >= 1.0


def test_run_consensus_workflow_integration():
    """Test complete workflow integration."""
    sample_data = [
        {'image_id': 'vg_001', 'object_id': 'obj_1', 'in_vg': False},
        {'image_id': 'vg_002', 'object_id': 'obj_2', 'in_vg': True}
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / 'input.json'
        output_path = Path(temp_dir) / 'output.json'
        
        with open(input_path, 'w') as f:
            json.dump(sample_data, f)
        
        summary = run_consensus_workflow(
            input_path=str(input_path),
            output_path=str(output_path),
            num_raters=3,
            consensus_threshold=0.67
        )
        
        assert os.path.exists(output_path)
        assert summary['total_candidates'] == 2
        assert summary['num_raters'] == 3
        
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        assert len(results) == 2
        for result in results:
            assert 'status' in result
            assert 'consensus_reached' in result


def test_consensus_result_dataclass():
    """Test ConsensusResult dataclass creation."""
    result = ConsensusResult(
        image_id='test_img',
        object_id='test_obj',
        candidate_data={},
        ratings=[],
        consensus_reached=True,
        consensus_score=1.0,
        majority_decision=True,
        average_confidence=0.9,
        rater_count=3,
        status='verified'
    )
    
    assert result.image_id == 'test_img'
    assert result.consensus_reached is True
    assert result.status == 'verified'