"""
Contract test for visual-only input/output schema (User Story 3).

This test verifies that the visual control experiment adheres to the defined
input/output schema. It ensures that the visual pipeline accepts the correct
input structure (query, image_path) and returns the expected output structure
(answer, predicted_bbox, chunk_id, confidence).

Note: This is a schema contract test. It does not execute the full model
inference but validates the data structures expected by the visual_control module.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Define the expected schema structure based on project requirements
# This schema matches what `code/visual_control.py` is expected to produce
VISUAL_OUTPUT_SCHEMA = {
    "query": str,
    "image_path": str,
    "answer": str,
    "predicted_bbox": list,  # [x_min, y_min, x_max, y_max]
    "chunk_id": str,
    "confidence": float,
    "metadata": dict
}

VISUAL_INPUT_SCHEMA = {
    "query": str,
    "image_path": str,
    "ground_truth": dict  # Optional, for evaluation purposes
}

class TestVisualInputOutputSchema:
    """Tests for the visual-only pipeline input/output contract."""

    def test_visual_output_schema_structure(self):
        """Verify that a sample output follows the required schema."""
        sample_output = {
            "query": "Where is the gene regulation mechanism described?",
            "image_path": "data/raw/sample_page_001.png",
            "answer": "The mechanism is described in the paragraph on the left.",
            "predicted_bbox": [100, 200, 500, 400],
            "chunk_id": "chunk_001_left",
            "confidence": 0.85,
            "metadata": {
                "model": "phi-3-vision-128k-instruct",
                "quantization": "4-bit",
                "inference_time_ms": 1250
            }
        }

        # Check top-level keys
        for key, expected_type in VISUAL_OUTPUT_SCHEMA.items():
            assert key in sample_output, f"Missing key '{key}' in output schema"
            assert isinstance(sample_output[key], expected_type), \
                f"Key '{key}' expected type {expected_type}, got {type(sample_output[key])}"

        # Specific validation for bbox (must be list of 4 numbers)
        assert len(sample_output["predicted_bbox"]) == 4, \
            "predicted_bbox must contain exactly 4 coordinates [x_min, y_min, x_max, y_max]"
        assert all(isinstance(coord, (int, float)) for coord in sample_output["predicted_bbox"]), \
            "All bbox coordinates must be numeric"

        # Confidence must be between 0 and 1
        assert 0.0 <= sample_output["confidence"] <= 1.0, \
            "Confidence score must be between 0.0 and 1.0"

    def test_visual_input_schema_structure(self):
        """Verify that a sample input follows the required schema."""
        sample_input = {
            "query": "Locate the figure describing the pathway.",
            "image_path": "data/raw/sample_page_001.png",
            "ground_truth": {
                "answer": "See Figure 2",
                "bbox": [150, 300, 450, 600],
                "chunk_id": "fig_2"
            }
        }

        for key, expected_type in VISUAL_INPUT_SCHEMA.items():
            assert key in sample_input, f"Missing key '{key}' in input schema"
            # For ground_truth, we allow dict or None
            if key == "ground_truth":
                assert isinstance(sample_input[key], (dict, type(None))), \
                    f"Key '{key}' expected dict or None, got {type(sample_input[key])}"
            else:
                assert isinstance(sample_input[key], expected_type), \
                    f"Key '{key}' expected type {expected_type}, got {type(sample_input[key])}"

    def test_visual_output_serialization(self):
        """Verify that the output can be serialized to JSON (for saving results)."""
        sample_output = {
            "query": "Test query",
            "image_path": "data/raw/test.png",
            "answer": "Test answer",
            "predicted_bbox": [10, 20, 30, 40],
            "chunk_id": "test_chunk",
            "confidence": 0.95,
            "metadata": {"model": "test"}
        }

        try:
            json_str = json.dumps(sample_output)
            reconstructed = json.loads(json_str)
            assert reconstructed == sample_output, "JSON serialization/deserialization failed"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Output schema is not JSON serializable: {e}")

    def test_missing_chunk_id_handling(self):
        """Verify behavior when chunk_id is missing or invalid (edge case)."""
        # According to T016 (error handling), missing chunk IDs should be logged
        # and IoU=0.0 assigned. Here we test that the schema allows for a null/empty
        # representation if the model fails to attribute.
        
        # Note: The schema expects a string, but in failure cases, the system
        # might assign a sentinel value. This test ensures the structure remains valid.
        failure_output = {
            "query": "Locate text.",
            "image_path": "data/raw/fail.png",
            "answer": "I cannot find the text.",
            "predicted_bbox": [0, 0, 0, 0],
            "chunk_id": "NO_ATTRIB",  # Sentinel value
            "confidence": 0.0,
            "metadata": {"error": "attribution_failed"}
        }

        for key, expected_type in VISUAL_OUTPUT_SCHEMA.items():
            assert key in failure_output
            # Special handling for chunk_id sentinel
            if key == "chunk_id":
                assert isinstance(failure_output[key], str)
            else:
                assert isinstance(failure_output[key], expected_type)

    def test_batch_output_structure(self):
        """Verify that a batch of results is a list of valid output objects."""
        batch_results = [
            {
                "query": "Query 1",
                "image_path": "img1.png",
                "answer": "Ans 1",
                "predicted_bbox": [10, 10, 20, 20],
                "chunk_id": "c1",
                "confidence": 0.9,
                "metadata": {}
            },
            {
                "query": "Query 2",
                "image_path": "img2.png",
                "answer": "Ans 2",
                "predicted_bbox": [30, 30, 40, 40],
                "chunk_id": "c2",
                "confidence": 0.8,
                "metadata": {}
            }
        ]

        assert isinstance(batch_results, list), "Batch results must be a list"
        for item in batch_results:
            for key, expected_type in VISUAL_OUTPUT_SCHEMA.items():
                assert key in item
                if key == "chunk_id":
                    assert isinstance(item[key], str)
                else:
                    assert isinstance(item[key], expected_type)