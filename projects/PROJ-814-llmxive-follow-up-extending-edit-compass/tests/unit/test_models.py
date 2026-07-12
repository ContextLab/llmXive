"""
Unit tests for data models.
"""
import pytest
from pydantic import ValidationError
from src.data_models import EditInstance, ScoreRecord

def test_edit_instance_creation():
    """Test that EditInstance can be created with valid data."""
    instance = EditInstance(
        source_image_path="/path/to/source.jpg",
        edited_image_path="/path/to/edited.jpg",
        instruction="Edit this image",
        category="World Knowledge Reasoning",
        human_judgment_score=0.8
    )
    
    assert instance.source_image_path == "/path/to/source.jpg"
    assert instance.category == "World Knowledge Reasoning"
    assert instance.human_judgment_score == 0.8

def test_edit_instance_validation():
    """Test that EditInstance validates required fields."""
    with pytest.raises(ValidationError):
        EditInstance(
            source_image_path="/path/to/source.jpg",
            # Missing other required fields
        )

def test_score_record_creation():
    """Test that ScoreRecord can be created with valid data."""
    record = ScoreRecord(
        instance_id="test-123",
        logic_score=0.7,
        fidelity_score=0.8,
        ssim=0.9,
        lpips=0.1,
        vllm_description="A description of the edited image",
        p_value_logic=0.01,
        p_value_fidelity=0.02,
        beta_logic=0.5,
        beta_fidelity=0.6
    )
    
    assert record.instance_id == "test-123"
    assert record.logic_score == 0.7
    assert record.fidelity_score == 0.8
    assert record.ssim == 0.9
    assert record.lpips == 0.1
    assert record.vllm_description == "A description of the edited image"

def test_score_record_validation():
    """Test that ScoreRecord validates required fields."""
    with pytest.raises(ValidationError):
        ScoreRecord(
            instance_id="test-123",
            # Missing other required fields
        )