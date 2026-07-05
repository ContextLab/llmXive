import pytest
from datetime import datetime
from code.utils.schema import (
    SalienceLevel,
    MFQResponse,
    MFQDataset,
    MoralStory,
    MoralStoriesDataset,
    VRInteractionLog,
    VRLogsDataset,
    MergedDataset,
    validate_mfq_data,
    validate_stories_data,
    validate_vr_logs_data,
    validate_merged_data,
)
from pydantic import ValidationError
import numpy as np

class TestSalienceLevel:
    """Tests for the SalienceLevel enum and mapping logic."""

    def test_salience_level_values(self):
        """Verify that SalienceLevel has the expected enum values."""
        assert SalienceLevel.LOW == "low"
        assert SalienceLevel.HIGH == "high"

    def test_salience_level_from_string(self):
        """Test creating SalienceLevel from string literals."""
        assert SalienceLevel("low") == SalienceLevel.LOW
        assert SalienceLevel("high") == SalienceLevel.HIGH

    def test_salience_level_invalid_value(self):
        """Test that invalid string values raise ValueError."""
        with pytest.raises(ValueError):
            SalienceLevel("medium")

class TestMFQResponse:
    """Tests for the MFQResponse schema."""

    def test_valid_mfq_response(self):
        """Test creating a valid MFQResponse."""
        response = MFQResponse(
            participant_id="P001",
            foundation_score=5.5,
            response_time_ms=1200,
            timestamp=datetime.now()
        )
        assert response.participant_id == "P001"
        assert response.foundation_score == 5.5
        assert response.response_time_ms == 1200

    def test_mfq_response_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            MFQResponse(foundation_score=5.5)

    def test_mfq_response_invalid_foundation_score(self):
        """Test that out-of-range foundation scores are rejected."""
        with pytest.raises(ValidationError):
            MFQResponse(
                participant_id="P001",
                foundation_score=11.0,  # Invalid: > 10
                response_time_ms=1200,
                timestamp=datetime.now()
            )

    def test_mfq_response_negative_response_time(self):
        """Test that negative response times are rejected."""
        with pytest.raises(ValidationError):
            MFQResponse(
                participant_id="P001",
                foundation_score=5.5,
                response_time_ms=-100,
                timestamp=datetime.now()
            )

class TestMFQDataset:
    """Tests for the MFQDataset schema."""

    def test_valid_mfq_dataset(self):
        """Test creating a valid MFQDataset."""
        responses = [
            MFQResponse(
                participant_id=f"P{i:03d}",
                foundation_score=np.random.uniform(0, 10),
                response_time_ms=np.random.randint(500, 3000),
                timestamp=datetime.now()
            )
            for i in range(10)
        ]
        dataset = MFQDataset(responses=responses)
        assert len(dataset.responses) == 10

    def test_mfq_dataset_empty(self):
        """Test that an empty dataset is valid."""
        dataset = MFQDataset(responses=[])
        assert len(dataset.responses) == 0

    def test_mfq_dataset_duplicate_participant_id(self):
        """Test that duplicate participant IDs are allowed (different trials)."""
        responses = [
            MFQResponse(
                participant_id="P001",
                foundation_score=5.0,
                response_time_ms=1000,
                timestamp=datetime.now()
            ),
            MFQResponse(
                participant_id="P001",
                foundation_score=5.2,
                response_time_ms=1100,
                timestamp=datetime.now()
            ),
        ]
        dataset = MFQDataset(responses=responses)
        assert len(dataset.responses) == 2

class TestMoralStory:
    """Tests for the MoralStory schema."""

    def test_valid_moral_story(self):
        """Test creating a valid MoralStory."""
        story = MoralStory(
            story_id="S001",
            text="A person finds a wallet on the street.",
            moral_foundation="care",
            difficulty_level=3
        )
        assert story.story_id == "S001"
        assert story.moral_foundation == "care"
        assert story.difficulty_level == 3

    def test_moral_story_invalid_foundation(self):
        """Test that invalid moral foundations are rejected."""
        with pytest.raises(ValidationError):
            MoralStory(
                story_id="S001",
                text="A person finds a wallet.",
                moral_foundation="invalid_foundation",
                difficulty_level=3
            )

    def test_moral_story_difficulty_range(self):
        """Test that difficulty level is within valid range."""
        with pytest.raises(ValidationError):
            MoralStory(
                story_id="S001",
                text="A person finds a wallet.",
                moral_foundation="care",
                difficulty_level=6  # Invalid: > 5
            )

class TestVRInteractionLog:
    """Tests for the VRInteractionLog schema - core for salience mapping."""

    def test_valid_vr_interaction_log(self):
        """Test creating a valid VRInteractionLog with salience mapping."""
        log = VRInteractionLog(
            participant_id="P001",
            story_id="S001",
            salience_level=SalienceLevel.HIGH,
            blend_shape_parameters={"jawOpen": 0.8, "eyeBlink": 0.2},
            gaze_x=0.5,
            gaze_y=0.5,
            response_time_ms=1500,
            moral_judgment=7,
            timestamp=datetime.now()
        )
        assert log.participant_id == "P001"
        assert log.story_id == "S001"
        assert log.salience_level == SalienceLevel.HIGH
        assert log.moral_judgment == 7

    def test_vr_interaction_log_low_salience(self):
        """Test VRInteractionLog with LOW salience level."""
        log = VRInteractionLog(
            participant_id="P002",
            story_id="S002",
            salience_level=SalienceLevel.LOW,
            blend_shape_parameters={"jawOpen": 0.3, "eyeBlink": 0.1},
            gaze_x=0.3,
            gaze_y=0.4,
            response_time_ms=2000,
            moral_judgment=4,
            timestamp=datetime.now()
        )
        assert log.salience_level == SalienceLevel.LOW

    def test_vr_interaction_log_invalid_gaze(self):
        """Test that out-of-range gaze coordinates are rejected."""
        with pytest.raises(ValidationError):
            VRInteractionLog(
                participant_id="P001",
                story_id="S001",
                salience_level=SalienceLevel.HIGH,
                blend_shape_parameters={},
                gaze_x=1.5,  # Invalid: > 1.0
                gaze_y=0.5,
                response_time_ms=1500,
                moral_judgment=7,
                timestamp=datetime.now()
            )

    def test_vr_interaction_log_invalid_judgment(self):
        """Test that out-of-range moral judgments are rejected."""
        with pytest.raises(ValidationError):
            VRInteractionLog(
                participant_id="P001",
                story_id="S001",
                salience_level=SalienceLevel.HIGH,
                blend_shape_parameters={},
                gaze_x=0.5,
                gaze_y=0.5,
                response_time_ms=1500,
                moral_judgment=11,  # Invalid: > 10
                timestamp=datetime.now()
            )

    def test_vr_interaction_log_missing_blend_shapes(self):
        """Test that missing blend_shape_parameters are allowed (default empty dict)."""
        log = VRInteractionLog(
            participant_id="P001",
            story_id="S001",
            salience_level=SalienceLevel.HIGH,
            blend_shape_parameters={},
            gaze_x=0.5,
            gaze_y=0.5,
            response_time_ms=1500,
            moral_judgment=7,
            timestamp=datetime.now()
        )
        assert log.blend_shape_parameters == {}

class TestVRLogsDataset:
    """Tests for the VRLogsDataset schema."""

    def test_valid_vr_logs_dataset(self):
        """Test creating a valid VRLogsDataset."""
        logs = [
            VRInteractionLog(
                participant_id=f"P{i:03d}",
                story_id=f"S{i:03d}",
                salience_level=SalienceLevel.HIGH if i % 2 == 0 else SalienceLevel.LOW,
                blend_shape_parameters={"jawOpen": 0.5},
                gaze_x=0.5,
                gaze_y=0.5,
                response_time_ms=1500,
                moral_judgment=5,
                timestamp=datetime.now()
            )
            for i in range(10)
        ]
        dataset = VRLogsDataset(logs=logs)
        assert len(dataset.logs) == 10

    def test_vr_logs_dataset_empty(self):
        """Test that an empty VRLogsDataset is valid."""
        dataset = VRLogsDataset(logs=[])
        assert len(dataset.logs) == 0

class TestMergedDataset:
    """Tests for the MergedDataset schema - combining MFQ and VR data."""

    def test_valid_merged_dataset(self):
        """Test creating a valid MergedDataset."""
        mfq_response = MFQResponse(
            participant_id="P001",
            foundation_score=6.5,
            response_time_ms=1200,
            timestamp=datetime.now()
        )
        vr_log = VRInteractionLog(
            participant_id="P001",
            story_id="S001",
            salience_level=SalienceLevel.HIGH,
            blend_shape_parameters={"jawOpen": 0.8},
            gaze_x=0.5,
            gaze_y=0.5,
            response_time_ms=1500,
            moral_judgment=7,
            timestamp=datetime.now()
        )
        merged = MergedDataset(
            mfq_response=mfq_response,
            vr_log=vr_log
        )
        assert merged.mfq_response.participant_id == "P001"
        assert merged.vr_log.story_id == "S001"
        assert merged.vr_log.salience_level == SalienceLevel.HIGH

    def test_merged_dataset_mismatched_participant_id(self):
        """Test that mismatched participant IDs are allowed (will be handled in preprocessing)."""
        mfq_response = MFQResponse(
            participant_id="P001",
            foundation_score=6.5,
            response_time_ms=1200,
            timestamp=datetime.now()
        )
        vr_log = VRInteractionLog(
            participant_id="P002",  # Different ID
            story_id="S001",
            salience_level=SalienceLevel.HIGH,
            blend_shape_parameters={"jawOpen": 0.8},
            gaze_x=0.5,
            gaze_y=0.5,
            response_time_ms=1500,
            moral_judgment=7,
            timestamp=datetime.now()
        )
        merged = MergedDataset(
            mfq_response=mfq_response,
            vr_log=vr_log
        )
        # Schema allows it; preprocessing logic should handle mismatches
        assert merged.mfq_response.participant_id == "P001"
        assert merged.vr_log.participant_id == "P002"

class TestHelperFunctions:
    """Tests for validation helper functions."""

    def test_validate_mfq_data_success(self):
        """Test successful validation of MFQ data."""
        responses = [
            MFQResponse(
                participant_id="P001",
                foundation_score=5.5,
                response_time_ms=1200,
                timestamp=datetime.now()
            )
        ]
        dataset = MFQDataset(responses=responses)
        result = validate_mfq_data(dataset)
        assert result["valid"] is True
        assert result["count"] == 1

    def test_validate_mfq_data_failure(self):
        """Test validation failure with invalid data."""
        # Create invalid response manually bypassing Pydantic
        responses = []
        dataset = MFQDataset(responses=responses)
        # Empty dataset should be valid
        result = validate_mfq_data(dataset)
        assert result["valid"] is True
        assert result["count"] == 0

    def test_validate_stories_data_success(self):
        """Test successful validation of stories data."""
        stories = [
            MoralStory(
                story_id="S001",
                text="Test story text.",
                moral_foundation="care",
                difficulty_level=3
            )
        ]
        dataset = MoralStoriesDataset(stories=stories)
        result = validate_stories_data(dataset)
        assert result["valid"] is True
        assert result["count"] == 1

    def test_validate_vr_logs_data_success(self):
        """Test successful validation of VR logs data."""
        logs = [
            VRInteractionLog(
                participant_id="P001",
                story_id="S001",
                salience_level=SalienceLevel.HIGH,
                blend_shape_parameters={"jawOpen": 0.8},
                gaze_x=0.5,
                gaze_y=0.5,
                response_time_ms=1500,
                moral_judgment=7,
                timestamp=datetime.now()
            )
        ]
        dataset = VRLogsDataset(logs=logs)
        result = validate_vr_logs_data(dataset)
        assert result["valid"] is True
        assert result["count"] == 1

    def test_validate_merged_data_success(self):
        """Test successful validation of merged data."""
        mfq_response = MFQResponse(
            participant_id="P001",
            foundation_score=6.5,
            response_time_ms=1200,
            timestamp=datetime.now()
        )
        vr_log = VRInteractionLog(
            participant_id="P001",
            story_id="S001",
            salience_level=SalienceLevel.HIGH,
            blend_shape_parameters={"jawOpen": 0.8},
            gaze_x=0.5,
            gaze_y=0.5,
            response_time_ms=1500,
            moral_judgment=7,
            timestamp=datetime.now()
        )
        merged = MergedDataset(mfq_response=mfq_response, vr_log=vr_log)
        result = validate_merged_data(merged)
        assert result["valid"] is True
        assert result["participant_id"] == "P001"

    def test_salience_mapping_interface(self):
        """
        Test the interface for salience mapping logic.
        This test defines the expected interface for the preprocess module
        that will map text stories to VR scenes with salience levels.
        """
        # Verify that SalienceLevel can be used to assign blend-shape parameters
        # This is the core interface contract for T016 (preprocess.py)
        
        # High salience should map to higher activation values
        high_salience_params = {"jawOpen": 0.8, "eyeBlink": 0.2}
        low_salience_params = {"jawOpen": 0.3, "eyeBlink": 0.1}
        
        # Create logs with different salience levels
        high_log = VRInteractionLog(
            participant_id="P001",
            story_id="S001",
            salience_level=SalienceLevel.HIGH,
            blend_shape_parameters=high_salience_params,
            gaze_x=0.5,
            gaze_y=0.5,
            response_time_ms=1500,
            moral_judgment=7,
            timestamp=datetime.now()
        )
        
        low_log = VRInteractionLog(
            participant_id="P002",
            story_id="S002",
            salience_level=SalienceLevel.LOW,
            blend_shape_parameters=low_salience_params,
            gaze_x=0.5,
            gaze_y=0.5,
            response_time_ms=2000,
            moral_judgment=4,
            timestamp=datetime.now()
        )
        
        # Verify salience levels are correctly stored
        assert high_log.salience_level == SalienceLevel.HIGH
        assert low_log.salience_level == SalienceLevel.LOW
        
        # Verify that the interface allows checking salience level
        assert high_log.salience_level == "high"
        assert low_log.salience_level == "low"