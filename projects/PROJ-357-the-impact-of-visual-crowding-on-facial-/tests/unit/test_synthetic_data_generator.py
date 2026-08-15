"""
Unit tests for synthetic data generator.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from analysis.synthetic_data_generator import (
    calculate_base_accuracy,
    generate_response,
    generate_synthetic_responses,
    load_manifest,
    EMOTION_CATEGORIES,
    BASE_ACCURACY_BY_EMOTION,
    CROWDING_PENALTY,
    ECCENTRICITY_PENALTY
)
import random

@pytest.fixture
def sample_manifest():
    """Create a temporary manifest file for testing."""
    manifest_data = [
        {
            'file_path': 'stimulus_001.png',
            'emotion': 'happy',
            'flanker_count': 6,
            'eccentricity': 4.0
        },
        {
            'file_path': 'stimulus_002.png',
            'emotion': 'fearful',
            'flanker_count': 9,
            'eccentricity': 6.0
        },
        {
            'file_path': 'stimulus_003.png',
            'emotion': 'neutral',
            'flanker_count': 3,
            'eccentricity': 2.0
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(manifest_data, f)
        return Path(f.name)

def test_calculate_base_accuracy_emotion_effect():
    """Test that different emotions have different base accuracies."""
    # Happy should have higher base accuracy than fearful
    happy_acc = calculate_base_accuracy('happy', 6, 4.0)
    fearful_acc = calculate_base_accuracy('fearful', 6, 4.0)
    
    assert happy_acc > fearful_acc, "Happy should be easier to recognize than fearful"
    assert 0.3 <= happy_acc <= 0.98, "Accuracy should be within valid range"
    assert 0.3 <= fearful_acc <= 0.98, "Accuracy should be within valid range"

def test_calculate_base_accuracy_crowding_effect():
    """Test that more flankers reduce accuracy."""
    low_crowding = calculate_base_accuracy('happy', 3, 4.0)
    high_crowding = calculate_base_accuracy('happy', 12, 4.0)
    
    assert low_crowding > high_crowding, "More flankers should reduce accuracy"

def test_calculate_base_accuracy_eccentricity_effect():
    """Test that higher eccentricity reduces accuracy."""
    low_ecc = calculate_base_accuracy('happy', 6, 2.0)
    high_ecc = calculate_base_accuracy('happy', 6, 8.0)
    
    assert low_ecc > high_ecc, "Higher eccentricity should reduce accuracy"

def test_generate_response_correctness():
    """Test that response generation respects accuracy probability."""
    rng = random.Random(42)
    true_label = 'happy'
    
    # With 90% accuracy, most responses should be correct
    correct_count = 0
    for _ in range(1000):
        response = generate_response(true_label, 'P001', 0.90, rng)
        if response == true_label:
            correct_count += 1
    
    accuracy = correct_count / 1000
    assert 0.85 <= accuracy <= 0.95, f"Accuracy should be close to 90%, got {accuracy}"

def test_generate_synthetic_responses_structure():
    """Test that generated responses have correct structure."""
    stimuli = [
        {
            'file_path': 'test_stimulus.png',
            'emotion': 'happy',
            'flanker_count': 6,
            'eccentricity': 4.0
        }
    ]
    
    responses = generate_synthetic_responses(stimuli, num_participants=5, seed=42)
    
    assert len(responses) == 5, "Should have 5 responses (one per participant)"
    
    required_fields = [
        'participant_id', 'stimulus_id', 'true_label', 
        'response_label', 'accuracy', 'flanker_count', 'eccentricity'
    ]
    
    for response in responses:
        for field in required_fields:
            assert field in response, f"Missing field: {field}"
        
        assert response['accuracy'] in [0, 1], "Accuracy should be 0 or 1"
        assert response['true_label'] == 'happy', "True label should match stimulus"
        assert response['flanker_count'] == 6, "Flanker count should match stimulus"
        assert response['eccentricity'] == 4.0, "Eccentricity should match stimulus"

def test_synthetic_responses_multiple_emotions():
    """Test generation across multiple emotion categories."""
    stimuli = [
        {'file_path': f's_{i}.png', 'emotion': emotion, 'flanker_count': 6, 'eccentricity': 4.0}
        for i, emotion in enumerate(['happy', 'sad', 'angry', 'fearful'])
    ]
    
    responses = generate_synthetic_responses(stimuli, num_participants=3, seed=123)
    
    # Should have 4 stimuli * 3 participants = 12 responses
    assert len(responses) == 12, "Should have 12 responses total"
    
    # Check that each emotion has responses
    emotions_in_responses = set(r['true_label'] for r in responses)
    assert len(emotions_in_responses) == 4, "Should have responses for all 4 emotions"

def test_synthetic_responses_accuracy_range():
    """Test that overall accuracy falls within expected range (60-90%)."""
    stimuli = [
        {'file_path': f's_{i}.png', 'emotion': emotion, 'flanker_count': 6, 'eccentricity': 4.0}
        for i, emotion in enumerate(EMOTION_CATEGORIES)
    ]
    
    responses = generate_synthetic_responses(stimuli, num_participants=10, seed=456)
    
    accuracy_values = [r['accuracy'] for r in responses]
    overall_accuracy = sum(accuracy_values) / len(accuracy_values)
    
    assert 0.50 <= overall_accuracy <= 0.95, f"Overall accuracy should be between 50-95%, got {overall_accuracy}"

def test_load_manifest(sample_manifest):
    """Test loading a manifest file."""
    stimuli = load_manifest(sample_manifest)
    
    assert len(stimuli) == 3, "Should load 3 stimuli"
    assert stimuli[0]['emotion'] == 'happy'
    assert stimuli[1]['emotion'] == 'fearful'
    
    # Clean up
    sample_manifest.unlink()

def test_synthetic_responses_participant_ids():
    """Test that participant IDs are unique and properly formatted."""
    stimuli = [
        {'file_path': 'test.png', 'emotion': 'happy', 'flanker_count': 6, 'eccentricity': 4.0}
    ]
    
    responses = generate_synthetic_responses(stimuli, num_participants=10, seed=789)
    
    participant_ids = [r['participant_id'] for r in responses]
    unique_ids = set(participant_ids)
    
    assert len(unique_ids) == 10, "Should have 10 unique participant IDs"
    assert all(pid.startswith('P') for pid in unique_ids), "Participant IDs should start with 'P'"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])