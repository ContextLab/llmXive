import pytest
from src.data.contracts.schemas import Message, AnalysisResult
from src.data.contracts.validators import validate_message, validate_analysis_result

class TestMessageSchema:
    def test_valid_message_creation(self):
        msg = Message(
            message_id="123",
            text="Hello 👋",
            emoji_present=True,
            emoji_count=1,
            emoji_types=["👋"],
            text_length=8,
            punctuation_count=0
        )
        assert msg.message_id == "123"
        assert msg.emoji_present is True
        assert msg.text_length == 8

    def test_message_no_emoji(self):
        msg = Message(
            message_id="456",
            text="No emoji here.",
            emoji_present=False,
            emoji_count=0,
            emoji_types=[],
            text_length=15,
            punctuation_count=1
        )
        assert msg.emoji_present is False
        assert msg.emoji_count == 0

    def test_message_validation_text_type(self):
        with pytest.raises(ValueError):
            Message(
                message_id="789",
                text=123, # Invalid type
                emoji_present=False,
                emoji_count=0,
                emoji_types=[],
                text_length=3,
                punctuation_count=0
            )

    def test_message_validation_emoji_types_list(self):
        with pytest.raises(ValueError):
            Message(
                message_id="999",
                text="Test",
                emoji_present=False,
                emoji_count=0,
                emoji_types="not_a_list", # Invalid type
                text_length=4,
                punctuation_count=0
            )

    def test_message_derived_text_length(self):
        msg = Message(
            message_id="auto",
            text="Calculated length",
            emoji_present=False,
            emoji_count=0,
            emoji_types=[],
            text_length=0, # Should be calculated
            punctuation_count=0
        )
        assert msg.text_length == 17

class TestAnalysisResultSchema:
    def test_valid_result_creation(self):
        res = AnalysisResult(
            analysis_id="A1",
            metric_name="correlation",
            effect_size=0.45,
            p_value=0.03,
            is_significant=True,
            sample_size=100
        )
        assert res.is_significant is True
        assert res.effect_size == 0.45

    def test_p_value_range_validation(self):
        with pytest.raises(ValueError):
            AnalysisResult(
                analysis_id="A2",
                metric_name="regression",
                effect_size=1.2,
                p_value=-0.1, # Invalid
                sample_size=50
            )

    def test_significance_derivation(self):
        res = AnalysisResult(
            analysis_id="A3",
            metric_name="test",
            effect_size=0.1,
            p_value=0.04,
            sample_size=100
            # is_significant not provided, should derive
        )
        assert res.is_significant is True

        res2 = AnalysisResult(
            analysis_id="A4",
            metric_name="test",
            effect_size=0.1,
            p_value=0.06,
            sample_size=100
        )
        assert res2.is_significant is False

class TestValidators:
    def test_validate_message_from_dict(self):
        data = {
            "message_id": "v1",
            "text": "Test",
            "emoji_present": False,
            "emoji_count": 0,
            "emoji_types": [],
            "text_length": 4,
            "punctuation_count": 0
        }
        msg = validate_message(data)
        assert isinstance(msg, Message)
        assert msg.message_id == "v1"

    def test_validate_message_from_object(self):
        msg_obj = Message(
            message_id="v2",
            text="Test",
            emoji_present=False,
            emoji_count=0,
            emoji_types=[],
            text_length=4,
            punctuation_count=0
        )
        result = validate_message(msg_obj)
        assert result is msg_obj

    def test_validate_message_missing_id(self):
        with pytest.raises(ValueError):
            validate_message({"text": "Test"})

    def test_validate_analysis_result_from_dict(self):
        data = {
            "analysis_id": "R1",
            "metric_name": "corr",
            "effect_size": 0.5,
            "p_value": 0.01,
            "sample_size": 100
        }
        res = validate_analysis_result(data)
        assert isinstance(res, AnalysisResult)
        assert res.analysis_id == "R1"

    def test_validate_analysis_result_missing_field(self):
        with pytest.raises(ValueError):
            validate_analysis_result({"analysis_id": "R2"})
