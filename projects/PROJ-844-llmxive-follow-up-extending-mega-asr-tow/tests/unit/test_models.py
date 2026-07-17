"""Unit tests for code/models.py"""
import pytest
from models import AudioClip, DistortionVector, StressCurve

def test_audio_clip_creation():
    """Verify AudioClip instantiation"""
    clip = AudioClip(
        path="test.wav",
        speaker_id="spk_001",
        transcript="Hello world",
        snr_bucket="high"
    )
    assert clip.path == "test.wav"
    assert clip.speaker_id == "spk_001"
    assert clip.transcript == "Hello world"

def test_distortion_vector_creation():
    """Verify DistortionVector instantiation"""
    vec = DistortionVector(
        snr_db=10.0,
        rt60_sec=0.4,
        vector_id="vec_001"
    )
    assert vec.snr_db == 10.0
    assert vec.rt60_sec == 0.4
    assert vec.vector_id == "vec_001"

def test_stress_curve_creation():
    """Verify StressCurve instantiation"""
    curve = StressCurve(
        clip_id="clip_001",
        vectors=[],
        results=[]
    )
    assert curve.clip_id == "clip_001"
    assert curve.vectors == []
    assert curve.results == []

def test_audio_clip_to_dict():
    """Verify AudioClip serialization"""
    clip = AudioClip(
        path="test.wav",
        speaker_id="spk_001",
        transcript="Test",
        snr_bucket="low"
    )
    d = clip.to_dict()
    assert d["path"] == "test.wav"
    assert d["speaker_id"] == "spk_001"
