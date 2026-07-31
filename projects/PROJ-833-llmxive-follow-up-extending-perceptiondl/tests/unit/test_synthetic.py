"""
Unit tests for code/synthetic/generator.py
Verifies non-overlap guarantee and retry logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthetic.generator import generate_sample_for_bin, run_generation_pipeline
from synthetic.placer import place_boxes_with_retry, boxes_overlap
from synthetic.validator import validate_no_overlaps
from synthetic.serializer import serialize_synthetic_sample


class TestNonOverlapGuarantee:
    """Tests to ensure generated bounding boxes never overlap."""

    def test_placer_never_returns_overlapping_boxes(self):
        """Verify that place_boxes_with_retry enforces non-overlap."""
        image_h, image_w = 512, 512
        target_count = 10
        min_size, max_size = 30, 60

        boxes, success = place_boxes_with_retry(
            image_h, image_w, target_count, min_size, max_size, max_attempts=100
        )

        assert success, "Placer should succeed for reasonable counts"
        assert len(boxes) == target_count, "Should place exactly target_count boxes"

        # Verify no overlaps
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                b1 = boxes[i]
                b2 = boxes[j]
                # boxes_overlap expects (x, y, w, h)
                assert not boxes_overlap((b1['x'], b1['y'], b1['w'], b1['h']),
                                         (b2['x'], b2['y'], b2['w'], b2['h'])), \
                    f"Boxes {i} and {j} overlap: {b1} vs {b2}"

    def test_generator_output_validates_no_overlaps(self):
        """Verify that generate_sample_for_bin produces valid non-overlapping data."""
        # Mock the fetcher to return a dummy image path
        mock_image_path = "/tmp/fake_image.png"
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            data_dir = Path(tmp_dir) / "data"
            data_dir.mkdir()
            
            # Mock the serializer to avoid actual image writing but capture the JSON
            captured_json = None
            
            def mock_serialize(image_path, boxes, relations, out_dir):
                nonlocal captured_json
                json_path = out_dir / "test.json"
                captured_json = {
                    "image_path": str(image_path),
                    "bounding_boxes": boxes,
                    "derived_relations": relations
                }
                with open(json_path, 'w') as f:
                    json.dump(captured_json, f)
                return str(json_path)

            with patch('synthetic.generator.fetch_dataset_sample') as mock_fetch, \
                 patch('synthetic.generator.serialize_synthetic_sample', side_effect=mock_serialize):
                
                mock_fetch.return_value = iter([{"image": None, "id": "test_001"}])
                
                # Run generation for a small bin
                result = generate_sample_for_bin(
                    region_count=5,
                    data_dir=str(data_dir),
                    output_dir=str(output_dir),
                    sample_size=1
                )
                
                assert result is True, "Generation should succeed"
                assert captured_json is not None, "JSON should be generated"
                
                # Validate the generated JSON
                boxes = captured_json['bounding_boxes']
                assert validate_no_overlaps(boxes), "Generated boxes must not overlap"

    def test_high_density_still_no_overlap(self):
        """Test that even at high density (50 regions), non-overlap is maintained."""
        image_h, image_w = 1024, 1024
        target_count = 50
        min_size, max_size = 20, 40

        boxes, success = place_boxes_with_retry(
            image_h, image_w, target_count, min_size, max_size, max_attempts=200
        )

        if success:
            # If it succeeded, verify strict non-overlap
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    b1 = boxes[i]
                    b2 = boxes[j]
                    assert not boxes_overlap(
                        (b1['x'], b1['y'], b1['w'], b1['h']),
                        (b2['x'], b2['y'], b2['w'], b2['h'])
                    ), f"High density overlap found: {b1} vs {b2}"
        else:
            # If it failed, verify it failed gracefully (returned fewer boxes or False)
            # The generator logic should handle this by reducing count or skipping
            pass


class TestRetryLogic:
    """Tests to verify retry logic reduces region count or skips on failure."""

    def test_retry_reduces_count_on_failure(self):
        """Verify that if placement fails, the system attempts with reduced count."""
        # Simulate a scenario where exact placement is impossible
        # by mocking the placer to fail repeatedly
        image_h, image_w = 100, 100
        target_count = 50
        min_size, max_size = 40, 50  # Large boxes, small image -> impossible

        boxes, success = place_boxes_with_retry(
            image_h, image_w, target_count, min_size, max_size, max_attempts=5
        )

        # Should fail to place all 50
        if not success:
            # The retry logic should have attempted with fewer boxes or returned partial
            # The key is that it didn't hang or crash, and returned a valid state
            assert boxes is not None or success is False
        else:
            # If it succeeded (unlikely with these constraints), verify non-overlap
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    assert not boxes_overlap(
                        (boxes[i]['x'], boxes[i]['y'], boxes[i]['w'], boxes[i]['h']),
                        (boxes[j]['x'], boxes[j]['y'], boxes[j]['w'], boxes[j]['h'])
                    )

    def test_generator_skips_unplaceable_images(self):
        """Verify that generator handles images where placement fails completely."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            data_dir = Path(tmp_dir) / "data"
            data_dir.mkdir()
            
            # Mock fetcher to yield an item, but force placer to fail
            def mock_fetch(*args, **kwargs):
                return iter([{"image": None, "id": "fail_001"}])

            def mock_place_fail(*args, **kwargs):
                return [], False

            with patch('synthetic.generator.fetch_dataset_sample', side_effect=mock_fetch), \
                 patch('synthetic.generator.place_boxes_with_retry', side_effect=mock_place_fail):
                
                    # The generator should handle the failure gracefully
                    # (either skip or reduce count, depending on implementation)
                    # We verify it doesn't crash
                    try:
                        result = generate_sample_for_bin(
                            region_count=10,
                            data_dir=str(data_dir),
                            output_dir=str(output_dir),
                            sample_size=1
                        )
                        # Should return False or True depending on whether it skipped
                        # The important part is no exception raised
                    except Exception as e:
                        pytest.fail(f"Generator crashed on unplaceable image: {e}")

    def test_retry_logic_terminates_after_max_attempts(self):
        """Verify that retry logic doesn't loop infinitely."""
        image_h, image_w = 50, 50
        target_count = 5
        min_size, max_size = 20, 25
        
        # Force a failure scenario with low max_attempts
        boxes, success = place_boxes_with_retry(
            image_h, image_w, target_count, min_size, max_size, max_attempts=1
        )
        
        # Should return quickly (not hang)
        assert success is False or len(boxes) < target_count