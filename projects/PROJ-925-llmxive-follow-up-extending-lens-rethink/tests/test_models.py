"""
Unit tests for data model entities.
"""
import pytest
from code.models.caption_record import CaptionRecord, CaptionRecordModel
from code.models.linguistic_feature_vector import LinguisticFeatureVector


class TestCaptionRecord:
    """Tests for CaptionRecord dataclass."""

    def test_caption_record_creation(self):
        """Test basic creation of a CaptionRecord."""
        record = CaptionRecord(
            caption_id="test-001",
            caption="A cat sits on the mat.",
            image_path="images/cat_001.jpg"
        )
        assert record.caption_id == "test-001"
        assert record.caption == "A cat sits on the mat."
        assert record.image_path == "images/cat_001.jpg"
        assert record.human_rating is None
        assert record.clip_score is None

    def test_caption_record_with_ratings(self):
        """Test CaptionRecord with optional fields populated."""
        record = CaptionRecord(
            caption_id="test-002",
            caption="A dog runs in the park.",
            human_rating=4.5,
            clip_score=0.85
        )
        assert record.human_rating == 4.5
        assert record.clip_score == 0.85


class TestCaptionRecordModel:
    """Tests for CaptionRecordModel Pydantic model."""

    def test_valid_model_creation(self):
        """Test creation of a valid CaptionRecordModel."""
        model = CaptionRecordModel(
            caption_id="test-003",
            caption="A bird flies in the sky.",
            human_rating=3.0,
            clip_score=0.75
        )
        assert model.caption_id == "test-003"
        assert model.human_rating == 3.0
        assert model.clip_score == 0.75

    def test_empty_caption_rejected(self):
        """Test that empty captions are rejected."""
        with pytest.raises(ValueError) as exc_info:
            CaptionRecordModel(
                caption_id="test-004",
                caption="   "
            )
        assert "Caption cannot be empty" in str(exc_info.value)

    def test_human_rating_bounds(self):
        """Test that human_rating respects 0.0-5.0 bounds."""
        with pytest.raises(ValueError):
            CaptionRecordModel(
                caption_id="test-005",
                caption="Test",
                human_rating=5.5
            )
        with pytest.raises(ValueError):
            CaptionRecordModel(
                caption_id="test-006",
                caption="Test",
                human_rating=-0.1
            )

    def test_clip_score_bounds(self):
        """Test that clip_score respects 0.0-1.0 bounds."""
        with pytest.raises(ValueError):
            CaptionRecordModel(
                caption_id="test-007",
                caption="Test",
                clip_score=1.1
            )
        with pytest.raises(ValueError):
            CaptionRecordModel(
                caption_id="test-008",
                caption="Test",
                clip_score=-0.01
            )


class TestLinguisticFeatureVector:
    """Tests for LinguisticFeatureVector Pydantic model."""

    def test_valid_vector_creation(self):
        """Test creation of a valid LinguisticFeatureVector."""
        vector = LinguisticFeatureVector(
            caption_id="feat-001",
            linguistic_uncertainty_proxy=2.5,
            syntactic_depth=5,
            noun_phrase_density=0.4,
            token_diversity=0.8
        )
        assert vector.caption_id == "feat-001"
        assert vector.linguistic_uncertainty_proxy == 2.5
        assert vector.syntactic_depth == 5
        assert vector.noun_phrase_density == 0.4
        assert vector.token_diversity == 0.8
        assert vector.caption_length_tokens is None
        assert vector.textual_description_complexity is None

    def test_with_optional_fields(self):
        """Test vector with optional fields populated."""
        vector = LinguisticFeatureVector(
            caption_id="feat-002",
            linguistic_uncertainty_proxy=1.2,
            syntactic_depth=3,
            noun_phrase_density=0.5,
            token_diversity=0.6,
            caption_length_tokens=15,
            textual_description_complexity=8
        )
        assert vector.caption_length_tokens == 15
        assert vector.textual_description_complexity == 8

    def test_nan_uncertainty_rejected(self):
        """Test that NaN uncertainty is rejected."""
        import math
        with pytest.raises(ValueError):
            LinguisticFeatureVector(
                caption_id="feat-003",
                linguistic_uncertainty_proxy=float('nan'),
                syntactic_depth=3,
                noun_phrase_density=0.5,
                token_diversity=0.6
            )

    def test_inf_uncertainty_rejected(self):
        """Test that Inf uncertainty is rejected."""
        with pytest.raises(ValueError):
            LinguisticFeatureVector(
                caption_id="feat-004",
                linguistic_uncertainty_proxy=float('inf'),
                syntactic_depth=3,
                noun_phrase_density=0.5,
                token_diversity=0.6
            )

    def test_noun_phrase_density_bounds(self):
        """Test noun_phrase_density bounds."""
        with pytest.raises(ValueError):
            LinguisticFeatureVector(
                caption_id="feat-005",
                linguistic_uncertainty_proxy=2.0,
                syntactic_depth=3,
                noun_phrase_density=1.5,
                token_diversity=0.6
            )
        with pytest.raises(ValueError):
            LinguisticFeatureVector(
                caption_id="feat-006",
                linguistic_uncertainty_proxy=2.0,
                syntactic_depth=3,
                noun_phrase_density=-0.1,
                token_diversity=0.6
            )

    def test_token_diversity_bounds(self):
        """Test token_diversity bounds."""
        with pytest.raises(ValueError):
            LinguisticFeatureVector(
                caption_id="feat-007",
                linguistic_uncertainty_proxy=2.0,
                syntactic_depth=3,
                noun_phrase_density=0.5,
                token_diversity=1.5
            )

    def test_syntactic_depth_minimum(self):
        """Test syntactic_depth minimum constraint (ge=1)."""
        with pytest.raises(ValueError):
            LinguisticFeatureVector(
                caption_id="feat-008",
                linguistic_uncertainty_proxy=2.0,
                syntactic_depth=0,
                noun_phrase_density=0.5,
                token_diversity=0.6
            )
        with pytest.raises(ValueError):
            LinguisticFeatureVector(
                caption_id="feat-009",
                linguistic_uncertainty_proxy=2.0,
                syntactic_depth=-1,
                noun_phrase_density=0.5,
                token_diversity=0.6
            )