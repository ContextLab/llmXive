"""
Unit tests for the stimulus generation module.
These tests verify the core logic of flanker positioning, overlap detection,
and stimulus creation without requiring the full RAVDESS dataset.
"""
import os
import sys
import json
import math
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
from PIL import Image

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.stimulus_gen import (
    generate_flanker_positions,
    check_flanker_overlap,
    create_stimulus,
    RAVDESS_EMOTIONS
)

class TestFlankerPositioning:
    """Tests for flanker position generation logic."""

    def test_position_count(self):
        """Verify that the requested number of flankers is generated."""
        positions = generate_flanker_positions(target_radius=128, eccentricity=2.0, count=5)
        assert len(positions) == 5, f"Expected 5 positions, got {len(positions)}"

    def test_eccentricity_range(self):
        """Verify that positions fall within the specified eccentricity range."""
        target_radius = 128
        eccentricity = 2.0
        positions = generate_flanker_positions(target_radius=target_radius, eccentricity=eccentricity, count=10)
        
        min_dist = target_radius + 32  # target_radius + flanker_size/2
        max_dist = eccentricity * target_radius
        
        for x, y in positions:
            dist = math.hypot(x, y)
            assert dist >= min_dist - 1, f"Position {x,y} is too close to target"
            assert dist <= max_dist + 1, f"Position {x,y} is too far from target"

    def test_no_target_overlap(self):
        """Verify that no flanker overlaps with the central target."""
        target_radius = 128
        flanker_radius = 32
        positions = generate_flanker_positions(target_radius=target_radius, eccentricity=1.5, count=20)
        
        for x, y in positions:
            dist = math.hypot(x, y)
            assert dist > target_radius + flanker_radius, f"Flanker at {x,y} overlaps with target"

    def test_no_mutual_overlap(self):
        """Verify that flankers do not overlap with each other."""
        positions = generate_flanker_positions(target_radius=128, eccentricity=2.5, count=10)
        flanker_radius = 32
        
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dx = positions[i][0] - positions[j][0]
                dy = positions[i][1] - positions[j][1]
                dist = math.hypot(dx, dy)
                assert dist >= 2 * flanker_radius - 1, f"Flankers {i} and {j} overlap"

class TestOverlapDetection:
    """Tests for overlap detection logic."""

    def test_target_overlap_detection(self):
        """Verify detection of flanker overlapping with target."""
        positions = [(100, 0)]  # Close to target (radius 128)
        target_radius = 128
        flanker_radius = 32
        
        assert check_flanker_overlap(positions, target_radius, flanker_radius) is True

    def test_mutual_overlap_detection(self):
        """Verify detection of flanker overlapping with another flanker."""
        positions = [(200, 0), (220, 0)]  # Very close to each other
        target_radius = 128
        flanker_radius = 32
        
        assert check_flanker_overlap(positions, target_radius, flanker_radius) is True

    def test_no_overlap(self):
        """Verify no overlap is detected when positions are valid."""
        positions = [(200, 0), (400, 0)]  # Well separated
        target_radius = 128
        flanker_radius = 32
        
        assert check_flanker_overlap(positions, target_radius, flanker_radius) is False

class TestStimulusCreation:
    """Tests for stimulus image creation."""

    def test_stimulus_dimensions(self):
        """Verify that the created stimulus has expected dimensions."""
        target_img = Image.new('RGB', (256, 256), color='red')
        positions = [(300, 0), (400, 0)]
        
        stimulus, status = create_stimulus(target_img, positions, flanker_count=2, eccentricity=2.0)
        
        assert stimulus.size[0] > 256, "Stimulus should be larger than target due to flankers"
        assert stimulus.size[1] > 256, "Stimulus should be larger than target due to flankers"
        assert status == "success"

    def test_stimulus_success_status(self):
        """Verify success status when all flankers are placed."""
        target_img = Image.new('RGB', (256, 256), color='blue')
        positions = [(300, 0), (300, 200), (300, -200)]
        
        stimulus, status = create_stimulus(target_img, positions, flanker_count=3, eccentricity=2.0)
        
        assert status == "success"

    def test_stimulus_exclusion_status(self):
        """Verify exclusion status when overlap occurs."""
        target_img = Image.new('RGB', (256, 256), color='green')
        # Positions that force overlap with target
        positions = [(100, 0)] 
        
        stimulus, status = create_stimulus(target_img, positions, flanker_count=1, eccentricity=1.0)
        
        # Should detect overlap with target
        assert "overlap" in status.lower() or status != "success"

class TestEmotionMapping:
    """Tests for emotion ID mapping."""

    def test_emotion_ids_exist(self):
        """Verify all expected emotion IDs are present."""
        expected_ids = [1, 2, 3, 4, 5, 6, 7, 8]
        for eid in expected_ids:
            assert eid in RAVDESS_EMOTIONS, f"Missing emotion ID: {eid}"

    def test_emotion_names(self):
        """Verify emotion names are correct."""
        assert RAVDESS_EMOTIONS[1] == "neutral"
        assert RAVDESS_EMOTIONS[3] == "happy"
        assert RAVDESS_EMOTIONS[5] == "angry"
        assert RAVDESS_EMOTIONS[8] == "surprised"