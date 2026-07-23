"""
Unit tests for core model classes in code/models.py.

Tests AudioClip, DistortionVector, and StressCurve dataclasses.
"""
import pytest
from pathlib import Path
import json
import numpy as np

# Import from sibling module
from models import AudioClip, DistortionVector, StressCurve


class TestAudioClip:
    """Tests for AudioClip dataclass."""

    def test_create_audio_clip(self):
        """Test creating an AudioClip instance."""
        clip = AudioClip(
            clip_id="test_clip_001",
            path="/path/to/audio.wav",
            transcript="This is a test transcript",
            speaker_id="speaker_123"
        )
        
        assert clip.clip_id == "test_clip_001"
        assert clip.path == "/path/to/audio.wav"
        assert clip.transcript == "This is a test transcript"
        assert clip.speaker_id == "speaker_123"

    def test_audio_clip_hash(self):
        """Test that AudioClip generates a consistent hash."""
        clip1 = AudioClip(
            clip_id="test_clip_001",
            path="/path/to/audio.wav",
            transcript="Same transcript",
            speaker_id="speaker_123"
        )
        clip2 = AudioClip(
            clip_id="test_clip_001",
            path="/path/to/audio.wav",
            transcript="Same transcript",
            speaker_id="speaker_123"
        )
        
        assert clip1.hash() == clip2.hash()

    def test_audio_clip_to_dict(self):
        """Test AudioClip serialization to dictionary."""
        clip = AudioClip(
            clip_id="test_clip_001",
            path="/path/to/audio.wav",
            transcript="Test",
            speaker_id="speaker_123"
        )
        
        data = clip.to_dict()
        assert data["clip_id"] == "test_clip_001"
        assert data["path"] == "/path/to/audio.wav"
        assert data["transcript"] == "Test"
        assert data["speaker_id"] == "speaker_123"


class TestDistortionVector:
    """Tests for DistortionVector dataclass."""

    def test_create_distortion_vector(self):
        """Test creating a DistortionVector instance."""
        vector = DistortionVector(
            vector_id="dist_001",
            snr_db=10.0,
            rt60=0.5,
            noise_type="white"
        )
        
        assert vector.vector_id == "dist_001"
        assert vector.snr_db == 10.0
        assert vector.rt60 == 0.5
        assert vector.noise_type == "white"

    def test_distortion_vector_hash(self):
        """Test that DistortionVector generates a consistent hash."""
        v1 = DistortionVector(
            vector_id="dist_001",
            snr_db=10.0,
            rt60=0.5,
            noise_type="white"
        )
        v2 = DistortionVector(
            vector_id="dist_001",
            snr_db=10.0,
            rt60=0.5,
            noise_type="white"
        )
        
        assert v1.hash() == v2.hash()

    def test_distortion_vector_to_dict(self):
        """Test DistortionVector serialization to dictionary."""
        vector = DistortionVector(
            vector_id="dist_001",
            snr_db=10.0,
            rt60=0.5,
            noise_type="white"
        )
        
        data = vector.to_dict()
        assert data["vector_id"] == "dist_001"
        assert data["snr_db"] == 10.0
        assert data["rt60"] == 0.5
        assert data["noise_type"] == "white"


class TestStressCurve:
    """Tests for StressCurve dataclass."""

    def test_create_stress_curve(self):
        """Test creating a StressCurve instance."""
        points = [
            {"intensity": 0.0, "sss": 1.0, "wer": 0.05},
            {"intensity": 0.5, "sss": 0.8, "wer": 0.15},
            {"intensity": 1.0, "sss": 0.2, "wer": 0.60}
        ]
        curve = StressCurve(
            clip_id="test_clip_001",
            model_id="whisper-tiny",
            scenario_id="scenario_001",
            points=points
        )
        
        assert curve.clip_id == "test_clip_001"
        assert curve.model_id == "whisper-tiny"
        assert curve.scenario_id == "scenario_001"
        assert len(curve.points) == 3

    def test_stress_curve_find_collapse(self):
        """Test finding collapse point in stress curve."""
        # Curve with clear collapse at intensity 0.8
        points = [
            {"intensity": 0.0, "sss": 1.0, "wer": 0.05},
            {"intensity": 0.5, "sss": 0.9, "wer": 0.10},
            {"intensity": 0.8, "sss": 0.4, "wer": 0.50},  # Collapse point
            {"intensity": 1.0, "sss": 0.1, "wer": 0.80}
        ]
        curve = StressCurve(
            clip_id="test_clip_001",
            model_id="whisper-tiny",
            scenario_id="scenario_001",
            points=points
        )
        
        # Threshold at 0.5 for SSS
        collapse_intensity = curve.find_collapse_threshold(0.5)
        assert collapse_intensity is not None
        assert collapse_intensity == 0.8

    def test_stress_curve_no_collapse(self):
        """Test stress curve with no collapse point."""
        points = [
            {"intensity": 0.0, "sss": 1.0, "wer": 0.05},
            {"intensity": 0.5, "sss": 0.8, "wer": 0.10},
            {"intensity": 1.0, "sss": 0.7, "wer": 0.15}
        ]
        curve = StressCurve(
            clip_id="test_clip_001",
            model_id="whisper-tiny",
            scenario_id="scenario_001",
            points=points
        )
        
        # Threshold at 0.5 - no point drops below
        collapse_intensity = curve.find_collapse_threshold(0.5)
        assert collapse_intensity is None

    def test_stress_curve_to_dict(self):
        """Test StressCurve serialization to dictionary."""
        points = [
            {"intensity": 0.0, "sss": 1.0, "wer": 0.05}
        ]
        curve = StressCurve(
            clip_id="test_clip_001",
            model_id="whisper-tiny",
            scenario_id="scenario_001",
            points=points
        )
        
        data = curve.to_dict()
        assert data["clip_id"] == "test_clip_001"
        assert data["model_id"] == "whisper-tiny"
        assert data["scenario_id"] == "scenario_001"
        assert "points" in data
