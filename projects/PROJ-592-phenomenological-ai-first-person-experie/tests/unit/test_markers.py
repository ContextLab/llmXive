import pytest
import json
import os
import sys
from pathlib import Path
import tempfile

# Add code/ to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.markers import (
    count_markers_in_text,
    compute_marker_scores,
    run_marker_analysis,
    MarkerError
)
from config import get_marker_dictionaries

class TestCountMarkersInText:
    def test_count_sensory_keywords(self):
        """Test counting sensory markers as per T032 requirement."""
        text = "I see the light and hear the sound. I feel the touch of the fabric."
        markers = ['see', 'hear', 'feel', 'touch', 'light', 'sound']
        
        count = count_markers_in_text(text, markers)
        # see, hear, feel, touch, light, sound = 6 matches
        assert count == 6

    def test_case_insensitivity(self):
        text = "I SEE the light and hear the SOUND."
        markers = ['see', 'sound']
        count = count_markers_in_text(text, markers)
        assert count == 2

    def test_whole_word_matching(self):
        """Ensure 'feel' doesn't match 'feeling'."""
        text = "I feel the feeling of warmth."
        markers = ['feel']
        count = count_markers_in_text(text, markers)
        # Only 'feel' should match, not 'feeling'
        assert count == 1

    def test_empty_text(self):
        text = ""
        markers = ['test']
        assert count_markers_in_text(text, markers) == 0

    def test_no_matches(self):
        text = "The quick brown fox jumps."
        markers = ['see', 'hear', 'feel']
        assert count_markers_in_text(text, markers) == 0

class TestComputeMarkerScores:
    def test_basic_computation(self):
        marker_dict = {
            'sensory': ['see', 'hear'],
            'temporal': ['now', 'then'],
            'intentional': ['think', 'believe']
        }
        text = "I see the light now and think about it."
        # see, now, think = 3 markers
        # Words: I, see, the, light, now, and, think, about, it = 9 words
        
        scores = compute_marker_scores(text, marker_dict)
        
        assert scores['sensory_count'] == 1  # see
        assert scores['temporal_count'] == 1  # now
        assert scores['intentional_count'] == 1  # think
        assert scores['total_markers'] == 3
        assert abs(scores['marker_density'] - (3/9)) < 0.001

    def test_empty_text_handling(self):
        marker_dict = {
            'sensory': ['see'],
            'temporal': ['now'],
            'intentional': ['think']
        }
        scores = compute_marker_scores("", marker_dict)
        
        assert scores['sensory_count'] == 0
        assert scores['total_markers'] == 0
        assert scores['marker_density'] == 0.0

class TestRunMarkerAnalysis:
    def test_full_pipeline(self):
        """Test the full analysis pipeline with a temporary file."""
        marker_dict = get_marker_dictionaries()
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            sample_data = [
                {"id": 1, "text": "I see the light now.", "strategy": "direct", "seed": 42},
                {"id": 2, "text": "I hear the sound and feel the touch.", "strategy": "role-play", "seed": 43}
            ]
            for item in sample_data:
                f.write(json.dumps(item) + '\n')
            input_path = f.name

        try:
            # Create temporary output path
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as out_f:
                output_path = out_f.name

            try:
                results = run_marker_analysis(input_path, output_path, marker_dict)
                
                assert len(results) == 2
                assert results[0]['report_id'] == 1
                assert results[0]['sensory_count'] > 0  # 'see', 'light'
                assert results[0]['strategy'] == 'direct'
                
                # Check file was written
                assert os.path.exists(output_path)
            finally:
                os.unlink(output_path)
        finally:
            os.unlink(input_path)

    def test_missing_file(self):
        with pytest.raises(MarkerError):
            run_marker_analysis("nonexistent.jsonl", "output.csv")

    def test_missing_text_field(self):
        marker_dict = get_marker_dictionaries()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Missing 'text' field
            f.write(json.dumps({"id": 1, "strategy": "direct"}) + '\n')
            input_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as out_f:
                output_path = out_f.name

            try:
                results = run_marker_analysis(input_path, output_path, marker_dict)
                # Should skip the report with missing text
                assert len(results) == 0
            finally:
                os.unlink(output_path)
        finally:
            os.unlink(input_path)

class TestMarkerDensity:
    def test_density_calculation(self):
        marker_dict = {
            'sensory': ['see'],
            'temporal': [],
            'intentional': []
        }
        # "I see" = 2 words, 1 marker -> density 0.5
        scores = compute_marker_scores("I see", marker_dict)
        assert abs(scores['marker_density'] - 0.5) < 0.001

    def test_long_text_normalization(self):
        marker_dict = {
            'sensory': ['see'],
            'temporal': [],
            'intentional': []
        }
        text = "I see " * 100  # 200 words, 100 markers -> density 0.5
        scores = compute_marker_scores(text, marker_dict)
        assert abs(scores['marker_density'] - 0.5) < 0.001