"""
Contract tests for data schema validation in the ingestion pipeline.

These tests verify that data produced by the ingestion scripts conforms to the
expected schema definitions before downstream processing. They validate:
1. Neural ROI timecourses CSV structure and data types
2. Event averages CSV structure and data types
3. Text story JSONL format and required fields
"""

import os
import sys
import json
import csv
import tempfile
from pathlib import Path
from typing import Dict, List, Any

import pytest
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.schema_validation import validate_neural_data, validate_text_data, validate_rsa_output
from utils.logging_config import get_logger, error


class TestNeuralDataSchema:
    """Contract tests for neural data schema validation."""

    def test_valid_roi_timecourses_schema(self):
        """Test that valid ROI timecourses pass schema validation."""
        # Create a temporary valid CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'roi', 'timepoint', 'signal'])
            writer.writerow(['sub-001', 'hippocampus_L', 0, 1.234])
            writer.writerow(['sub-001', 'hippocampus_L', 1, 1.245])
            writer.writerow(['sub-001', 'hippocampus_R', 0, 1.123])
            writer.writerow(['sub-001', 'dlpfc', 0, 0.987])
            temp_path = f.name

        try:
            result = validate_neural_data(temp_path)
            assert result is True, "Valid ROI timecourses should pass validation"
        finally:
            os.unlink(temp_path)

    def test_missing_required_columns_roi(self):
        """Test that missing required columns fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            # Missing 'signal' column
            writer.writerow(['subject_id', 'roi', 'timepoint'])
            writer.writerow(['sub-001', 'hippocampus_L', 0])
            temp_path = f.name

        try:
            result = validate_neural_data(temp_path)
            assert result is False, "Missing required columns should fail validation"
        finally:
            os.unlink(temp_path)

    def test_invalid_data_types_roi(self):
        """Test that invalid data types in signal column fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'roi', 'timepoint', 'signal'])
            writer.writerow(['sub-001', 'hippocampus_L', 0, 'invalid_float'])
            temp_path = f.name

        try:
            result = validate_neural_data(temp_path)
            assert result is False, "Invalid data types should fail validation"
        finally:
            os.unlink(temp_path)

    def test_empty_file_roi(self):
        """Test that empty files fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write only header, no data
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'roi', 'timepoint', 'signal'])
            temp_path = f.name

        try:
            result = validate_neural_data(temp_path)
            assert result is False, "Empty data files should fail validation"
        finally:
            os.unlink(temp_path)

    def test_valid_event_averages_schema(self):
        """Test that valid event averages pass schema validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'event_id', 'roi', 'mean_signal'])
            writer.writerow(['sub-001', 'evt_001', 'hippocampus_L', 1.234])
            writer.writerow(['sub-001', 'evt_001', 'hippocampus_R', 1.123])
            writer.writerow(['sub-001', 'evt_002', 'dlpfc', 0.987])
            temp_path = f.name

        try:
            result = validate_neural_data(temp_path)
            assert result is True, "Valid event averages should pass validation"
        finally:
            os.unlink(temp_path)

    def test_missing_required_columns_event(self):
        """Test that missing required columns in event averages fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            # Missing 'mean_signal' column
            writer.writerow(['subject_id', 'event_id', 'roi'])
            writer.writerow(['sub-001', 'evt_001', 'hippocampus_L'])
            temp_path = f.name

        try:
            result = validate_neural_data(temp_path)
            assert result is False, "Missing required columns should fail validation"
        finally:
            os.unlink(temp_path)


class TestTextDataSchema:
    """Contract tests for text data schema validation."""

    def test_valid_jsonl_schema(self):
        """Test that valid JSONL file passes schema validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"story_id": "story_001", "text": "Once upon a time...", "source": "rocstories"}\n')
            f.write('{"story_id": "story_002", "text": "The end.", "source": "rocstories"}\n')
            temp_path = f.name

        try:
            result = validate_text_data(temp_path)
            assert result is True, "Valid JSONL should pass validation"
        finally:
            os.unlink(temp_path)

    def test_missing_required_fields_jsonl(self):
        """Test that missing required fields fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Missing 'text' field
            f.write('{"story_id": "story_001", "source": "rocstories"}\n')
            temp_path = f.name

        try:
            result = validate_text_data(temp_path)
            assert result is False, "Missing required fields should fail validation"
        finally:
            os.unlink(temp_path)

    def test_invalid_json_line(self):
        """Test that invalid JSON lines fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"story_id": "story_001", "text": "Valid line"}\n')
            f.write('invalid json line\n')
            temp_path = f.name

        try:
            result = validate_text_data(temp_path)
            assert result is False, "Invalid JSON lines should fail validation"
        finally:
            os.unlink(temp_path)

    def test_empty_jsonl_file(self):
        """Test that empty JSONL files fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Empty file
            temp_path = f.name

        try:
            result = validate_text_data(temp_path)
            assert result is False, "Empty JSONL files should fail validation"
        finally:
            os.unlink(temp_path)


class TestRSAOutputSchema:
    """Contract tests for RSA output schema validation."""

    def test_valid_rsa_matrix_schema(self):
        """Test that valid RSA matrix passes schema validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['condition_1', 'condition_2', 'distance', 'p_value'])
            writer.writerow(['story_A', 'story_B', 0.123, 0.05])
            writer.writerow(['story_A', 'story_C', 0.456, 0.01])
            temp_path = f.name

        try:
            result = validate_rsa_output(temp_path)
            assert result is True, "Valid RSA matrix should pass validation"
        finally:
            os.unlink(temp_path)

    def test_missing_required_columns_rsa(self):
        """Test that missing required columns in RSA output fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            # Missing 'p_value' column
            writer.writerow(['condition_1', 'condition_2', 'distance'])
            writer.writerow(['story_A', 'story_B', 0.123])
            temp_path = f.name

        try:
            result = validate_rsa_output(temp_path)
            assert result is False, "Missing required columns should fail validation"
        finally:
            os.unlink(temp_path)

    def test_invalid_distance_value(self):
        """Test that negative distance values fail validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['condition_1', 'condition_2', 'distance', 'p_value'])
            writer.writerow(['story_A', 'story_B', -0.123, 0.05])
            temp_path = f.name

        try:
            result = validate_rsa_output(temp_path)
            assert result is False, "Negative distance values should fail validation"
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])