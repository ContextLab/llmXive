"""
Unit tests for the base data models defined in src/data/models.py.
"""

import pytest
from src.data.models import Image, Object, ParticipantRecall, VerificationStatus


class TestImage:
    def test_image_creation_valid(self):
        img = Image(
            image_id="12345",
            url="http://example.com/img.jpg",
            width=800,
            height=600
        )
        assert img.image_id == "12345"
        assert img.width == 800
        assert img.height == 600

    def test_image_creation_invalid_dimensions(self):
        with pytest.raises(ValueError):
            Image(
                image_id="12345",
                url="http://example.com/img.jpg",
                width=-10,
                height=600
            )

    def test_image_metadata_default(self):
        img = Image(
            image_id="12345",
            url="http://example.com/img.jpg",
            width=800,
            height=600
        )
        assert img.metadata == {}

    def test_image_metadata_custom(self):
        img = Image(
            image_id="12345",
            url="http://example.com/img.jpg",
            width=800,
            height=600,
            metadata={"source": "visual_genome"}
        )
        assert img.metadata["source"] == "visual_genome"


class TestObject:
    def test_object_creation_valid(self):
        obj = Object(
            object_id="obj_001",
            image_id="12345",
            label="dog",
            bbox={"x": 10, "y": 20, "width": 50, "height": 50}
        )
        assert obj.object_id == "obj_001"
        assert obj.label == "dog"
        assert obj.verification_status == VerificationStatus.PENDING

    def test_object_to_dict(self):
        obj = Object(
            object_id="obj_001",
            image_id="12345",
            label="dog",
            bbox={"x": 10, "y": 20, "width": 50, "height": 50},
            is_false_memory=True,
            verification_status=VerificationStatus.VERIFIED
        )
        data = obj.to_dict()
        assert data["object_id"] == "obj_001"
        assert data["is_false_memory"] is True
        assert data["verification_status"] == "verified"


class TestParticipantRecall:
    def test_recall_creation_empty(self):
        recall = ParticipantRecall(
            participant_id="p_001",
            image_id="12345"
        )
        assert recall.recalled_objects == []

    def test_add_recalled_object(self):
        recall = ParticipantRecall(
            participant_id="p_001",
            image_id="12345"
        )
        recall.add_recalled_object("dog")
        recall.add_recalled_object("cat")
        assert len(recall.recalled_objects) == 2
        assert "dog" in recall.recalled_objects

    def test_add_duplicate_recalled_object(self):
        recall = ParticipantRecall(
            participant_id="p_001",
            image_id="12345"
        )
        recall.add_recalled_object("dog")
        recall.add_recalled_object("dog")
        assert len(recall.recalled_objects) == 1

    def test_has_recalled(self):
        recall = ParticipantRecall(
            participant_id="p_001",
            image_id="12345",
            recalled_objects=["dog", "cat"]
        )
        assert recall.has_recalled("dog") is True
        assert recall.has_recalled("bird") is False

    def test_recall_to_dict(self):
        recall = ParticipantRecall(
            participant_id="p_001",
            image_id="12345",
            recalled_objects=["dog", "cat"],
            timestamp="2023-10-01T12:00:00Z",
            session_id="sess_001"
        )
        data = recall.to_dict()
        assert data["participant_id"] == "p_001"
        assert len(data["recalled_objects"]) == 2
        assert data["timestamp"] == "2023-10-01T12:00:00Z"