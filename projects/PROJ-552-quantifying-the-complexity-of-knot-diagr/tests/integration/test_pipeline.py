"""Integration test for the Knot Atlas download pipeline.

This test validates the end-to-end flow of:
1. Downloading knot data from Knot Atlas
2. Parsing the downloaded data
3. Validating the parsed data
4. Saving raw and cleaned data

Per T012 specification: Integration test for download pipeline in
tests/integration/test_pipeline.py
"""

import json
import csv
import pytest
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock, mock_open

# Import from existing API surface
from download.knot_atlas_loader import (
    KnotRecord,
    DownloadFailure,
    KnotAtlasDownloader,
    download_knot_atlas_data,
    verify_downloaded_record,
    verify_retry_logic,
)
from data.parser import ParsedKnotData, parse_knot_atlas_data
from data.validator import (
    check_null_values,
    check_format_validity,
    check_duplicate_records,
    validate_dataset_data_quality,
)
from data.data_saver import save_raw_and_cleaned_data


class MockResponse:
    """Mock HTTP response for testing download functionality."""

    def __init__(
        self,
        json_data: Optional[Dict] = None,
        text: Optional[str] = None,
        status_code: int = 200,
        raise_for_status_side_effect: Optional[Exception] = None,
    ):
        self._json_data = json_data
        self._text = text
        self.status_code = status_code
        self._raise_for_status_side_effect = raise_for_status_side_effect

    def json(self):
        if self._raise_for_status_side_effect:
            raise self._raise_for_status_side_effect
        return self._json_data

    def raise_for_status(self):
        if self._raise_for_status_side_effect:
            raise self._raise_for_status_side_effect

    @property
    def text(self):
        return self._text


class TestDownloadPipelineIntegration:
    """Integration tests for the complete download pipeline."""

    @pytest.fixture
    def sample_knot_record(self) -> Dict[str, Any]:
        """Sample Knot Atlas record for testing."""
        return {
            "name": "3_1",
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": 0.533349,
            "is_alternating": True,
            "dt_code": "2 2 -4",
            "braid_word": "1 -1",
        }

    @pytest.fixture
    def sample_multiple_knots(self) -> List[Dict[str, Any]]:
        """Sample multiple knot records for testing."""
        return [
            {
                "name": "3_1",
                "crossing_number": 3,
                "braid_index": 2,
                "hyperbolic_volume": 0.533349,
                "is_alternating": True,
                "dt_code": "2 2 -4",
                "braid_word": "1 -1",
            },
            {
                "name": "4_1",
                "crossing_number": 4,
                "braid_index": 2,
                "hyperbolic_volume": 2.029883,
                "is_alternating": True,
                "dt_code": "4 4 -4",
                "braid_word": "1 -1 1 -1",
            },
            {
                "name": "5_1",
                "crossing_number": 5,
                "braid_index": 2,
                "hyperbolic_volume": 3.163963,
                "is_alternating": True,
                "dt_code": "2 2 2 2 -4",
                "braid_word": "1 -1 1 -1 1 -1",
            },
        ]

    @pytest.fixture
    def temp_data_dir(self, tmp_path: Path) -> Path:
        """Create a temporary data directory structure."""
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        return tmp_path

    def test_download_and_parse_integration(
        self, sample_knot_record, temp_data_dir
    ):
        """Test end-to-end download and parsing integration."""
        # Mock the HTTP request to return sample data
        mock_response = MockResponse(json_data=sample_knot_record)

        with patch("download.knot_atlas_loader.requests.get") as mock_get:
            mock_get.return_value = mock_response

            # Step 1: Download data
            downloader = KnotAtlasDownloader(base_url="https://katlas.org")
            download_result = downloader.download_knot_record("3_1")

            # Verify download succeeded
            assert download_result is not None
            assert isinstance(download_result, KnotRecord)
            assert download_result.name == "3_1"
            assert download_result.crossing_number == 3

            # Step 2: Parse the downloaded data
            parsed_data = parse_knot_atlas_data([download_result])

            # Verify parsing succeeded
            assert len(parsed_data) == 1
            assert isinstance(parsed_data[0], ParsedKnotData)
            assert parsed_data[0].name == "3_1"
            assert parsed_data[0].crossing_number == 3
            assert parsed_data[0].braid_index == 2

    def test_download_retry_logic_integration(self, temp_data_dir):
        """Test retry logic with simulated failures."""
        # Mock requests.get to fail twice then succeed
        call_count = [0]

        def mock_get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                return MockResponse(
                    status_code=500,
                    raise_for_status_side_effect=Exception("Server Error"),
                )
            return MockResponse(
                json_data={
                    "name": "3_1",
                    "crossing_number": 3,
                    "braid_index": 2,
                    "hyperbolic_volume": 0.533349,
                    "is_alternating": True,
                    "dt_code": "2 2 -4",
                    "braid_word": "1 -1",
                }
            )

        with patch("download.knot_atlas_loader.requests.get") as mock_get:
            mock_get.side_effect = mock_get_side_effect

            # Download should succeed after retries
            downloader = KnotAtlasDownloader(
                base_url="https://katlas.org",
                initial_delay=0.001,  # Fast retry for testing
                max_delay=0.01,
                multiplier=2,
                max_retries=3,
            )
            download_result = downloader.download_knot_record("3_1")

            # Verify retry was attempted (at least 3 calls)
            assert mock_get.call_count >= 3
            # Verify download eventually succeeded
            assert download_result is not None
            assert download_result.name == "3_1"

    def test_parse_and_validate_integration(
        self, sample_multiple_knots, temp_data_dir
    ):
        """Test parsing followed by validation integration."""
        # Step 1: Create download records
        records = [KnotRecord(**knot_data) for knot_data in sample_multiple_knots]

        # Step 2: Parse the records
        parsed_data = parse_knot_atlas_data(records)

        # Verify parsing
        assert len(parsed_data) == 3
        for parsed in parsed_data:
            assert parsed.crossing_number > 0
            assert parsed.braid_index > 0
            assert parsed.braid_index <= parsed.crossing_number

        # Step 3: Validate the parsed data
        validation_result = validate_dataset_data_quality(parsed_data)

        # Verify validation succeeded
        assert validation_result is not None
        assert validation_result.null_count == 0
        assert validation_result.duplicate_count == 0

    def test_full_pipeline_save_integration(
        self, sample_multiple_knots, temp_data_dir
    ):
        """Test complete pipeline: download -> parse -> validate -> save."""
        # Step 1: Create download records
        records = [KnotRecord(**knot_data) for knot_data in sample_multiple_knots]

        # Step 2: Parse the records
        parsed_data = parse_knot_atlas_data(records)

        # Step 3: Validate the parsed data
        validation_result = validate_dataset_data_quality(parsed_data)

        # Step 4: Save raw and cleaned data
        raw_path = temp_data_dir / "data" / "raw" / "knot_atlas_raw.json"
        cleaned_path = (
            temp_data_dir / "data" / "processed" / "knots_cleaned.csv"
        )

        save_raw_and_cleaned_data(
            records=records,
            parsed_data=parsed_data,
            raw_output_path=raw_path,
            cleaned_output_path=cleaned_path,
        )

        # Verify files were created
        assert raw_path.exists(), "Raw data file should exist"
        assert cleaned_path.exists(), "Cleaned data file should exist"

        # Verify raw data content
        with open(raw_path, "r") as f:
            raw_data = json.load(f)
            assert len(raw_data) == 3
            assert raw_data[0]["name"] == "3_1"

        # Verify cleaned data content
        with open(cleaned_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3
            assert rows[0]["name"] == "3_1"
            assert int(rows[0]["crossing_number"]) == 3

    def test_hyperbolic_volume_parsing_integration(
        self, temp_data_dir
    ):
        """Test that hyperbolic volume is correctly parsed and preserved."""
        knot_with_volume = {
            "name": "5_2",
            "crossing_number": 5,
            "braid_index": 2,
            "hyperbolic_volume": 2.828427,
            "is_alternating": False,
            "dt_code": "6 2 -4",
            "braid_word": "1 -1 1 -1 1",
        }

        record = KnotRecord(**knot_with_volume)
        parsed_data = parse_knot_atlas_data([record])

        assert len(parsed_data) == 1
        assert parsed_data[0].hyperbolic_volume == 2.828427

    def test_alternating_classification_integration(
        self, temp_data_dir
    ):
        """Test that alternating classification is correctly parsed."""
        alternating_knot = {
            "name": "3_1",
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": 0.533349,
            "is_alternating": True,
            "dt_code": "2 2 -4",
            "braid_word": "1 -1",
        }

        non_alternating_knot = {
            "name": "8_19",
            "crossing_number": 8,
            "braid_index": 3,
            "hyperbolic_volume": 5.333349,
            "is_alternating": False,
            "dt_code": "4 4 4 4 -4 -4",
            "braid_word": "1 -1 1 -1 1 1",
        }

        records = [
            KnotRecord(**alternating_knot),
            KnotRecord(**non_alternating_knot),
        ]
        parsed_data = parse_knot_atlas_data(records)

        assert parsed_data[0].is_alternating is True
        assert parsed_data[1].is_alternating is False

    def test_braid_index_constraint_integration(
        self, temp_data_dir
    ):
        """Test that braid index <= crossing number constraint holds."""
        # Create records with valid braid indices
        valid_knots = [
            {
                "name": f"{n}_{i}",
                "crossing_number": n,
                "braid_index": min(n, 3),  # Ensure braid_index <= crossing_number
                "hyperbolic_volume": 0.5,
                "is_alternating": True,
                "dt_code": "2",
                "braid_word": "1",
            }
            for n in range(3, 14)
            for i in range(1)
        ]

        records = [KnotRecord(**knot_data) for knot_data in valid_knots]
        parsed_data = parse_knot_atlas_data(records)

        # Verify constraint holds for all parsed records
        for parsed in parsed_data:
            assert parsed.braid_index <= parsed.crossing_number, (
                f"Braid index {parsed.braid_index} > "
                f"crossing number {parsed.crossing_number} for {parsed.name}"
            )

    def test_null_value_detection_integration(
        self, temp_data_dir
    ):
        """Test that null values are correctly detected during validation."""
        # Create a record with null values
        record_with_nulls = {
            "name": "test_knot",
            "crossing_number": None,
            "braid_index": 2,
            "hyperbolic_volume": None,
            "is_alternating": True,
            "dt_code": "2 2 -4",
            "braid_word": "1 -1",
        }

        record = KnotRecord(**record_with_nulls)
        parsed_data = parse_knot_atlas_data([record])

        # Validate and check for null detection
        validation_result = validate_dataset_data_quality(parsed_data)

        # Should detect null crossing_number and hyperbolic_volume
        assert validation_result.null_count > 0

    def test_duplicate_detection_integration(
        self, temp_data_dir
    ):
        """Test that duplicate records are correctly detected."""
        # Create duplicate records
        duplicate_data = {
            "name": "3_1",
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": 0.533349,
            "is_alternating": True,
            "dt_code": "2 2 -4",
            "braid_word": "1 -1",
        }

        records = [
            KnotRecord(**duplicate_data),
            KnotRecord(**duplicate_data),
        ]
        parsed_data = parse_knot_atlas_data(records)

        # Validate and check for duplicate detection
        validation_result = validate_dataset_data_quality(parsed_data)

        # Should detect duplicate records
        assert validation_result.duplicate_count > 0

    def test_crossing_number_range_integration(
        self, temp_data_dir
    ):
        """Test that crossing numbers are within expected range (≤13)."""
        valid_knots = [
            {
                "name": f"{n}_{i}",
                "crossing_number": n,
                "braid_index": min(n, 3),
                "hyperbolic_volume": 0.5,
                "is_alternating": True,
                "dt_code": "2",
                "braid_word": "1",
            }
            for n in range(3, 14)
            for i in range(1)
        ]

        invalid_knot = {
            "name": "14_1",
            "crossing_number": 14,  # Exceeds expected max
            "braid_index": 3,
            "hyperbolic_volume": 0.5,
            "is_alternating": True,
            "dt_code": "2",
            "braid_word": "1",
        }

        records = [KnotRecord(**k) for k in valid_knots]
        records.append(KnotRecord(**invalid_knot))
        parsed_data = parse_knot_atlas_data(records)

        # Check value ranges
        range_check = check_value_ranges(parsed_data)

        # Should detect the out-of-range crossing number
        assert range_check is not None

    def test_dataset_enumeration_integration(
        self, sample_multiple_knots, temp_data_dir
    ):
        """Test that dataset enumeration captures all required fields."""
        records = [KnotRecord(**knot_data) for knot_data in sample_multiple_knots]
        parsed_data = parse_knot_atlas_data(records)

        # Verify all required fields are present
        required_fields = [
            "name",
            "crossing_number",
            "braid_index",
            "hyperbolic_volume",
            "is_alternating",
        ]

        for parsed in parsed_data:
            for field in required_fields:
                assert hasattr(parsed, field), (
                    f"Missing required field: {field}"
                )

    def test_data_quality_flags_integration(
        self, temp_data_dir
    ):
        """Test that data quality flags are correctly generated."""
        # Create records with various quality issues
        mixed_data = [
            {
                "name": "good_knot",
                "crossing_number": 3,
                "braid_index": 2,
                "hyperbolic_volume": 0.533349,
                "is_alternating": True,
                "dt_code": "2 2 -4",
                "braid_word": "1 -1",
            },
            {
                "name": "null_knot",
                "crossing_number": None,
                "braid_index": 2,
                "hyperbolic_volume": None,
                "is_alternating": True,
                "dt_code": "2 2 -4",
                "braid_word": "1 -1",
            },
        ]

        records = [KnotRecord(**k) for k in mixed_data]
        parsed_data = parse_knot_atlas_data(records)

        # Validate and verify flags are generated
        validation_result = validate_dataset_data_quality(parsed_data)

        # Should have flags for null values
        assert validation_result is not None
        assert validation_result.null_count > 0