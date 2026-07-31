"""
Unit tests for code/synthetic/generator.py

Tests verify:
- Non-overlap guarantee
- Retry logic behavior
- Schema compliance
- Relation derivation correctness
"""
import json
import sys
import math
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from synthetic.generator import generate_sample_for_bin, run_generation_pipeline
from synthetic.placer import place_boxes_with_retry
from synthetic.deriver import derive_all_relations
from synthetic.validator import validate_no_overlaps
from synthetic.serializer import serialize_synthetic_sample

class TestNonOverlapGuarantee:
    """Test that generated boxes never overlap."""

    def test_place_boxes_no_overlap(self):
        """Verify place_boxes_with_retry returns non-overlapping boxes."""
        image_size = (800, 600)
        target_count = 30
        max_retries = 10

        boxes = place_boxes_with_retry(
            image_size=image_size,
            target_count=target_count,
            max_retries=max_retries
        )

        if boxes is not None:
            assert len(boxes) == target_count, f"Expected {target_count} boxes, got {len(boxes)}"
            assert validate_no_overlaps(boxes), "Generated boxes have overlaps"

    def test_place_boxes_retry_on_failure(self):
        """Verify retry logic reduces count when placement fails."""
        # This is a behavioral test - if placement fails for high density,
        # the function should either reduce count or return None
        image_size = (100, 100)  # Very small image
        target_count = 100  # Impossible to fit 100 boxes
        max_retries = 5

        boxes = place_boxes_with_retry(
            image_size=image_size,
            target_count=target_count,
            max_retries=max_retries
        )

        # Should return None or fewer boxes, never overlapping
        if boxes is not None:
            assert validate_no_overlaps(boxes), "Boxes overlap after retries"
            assert len(boxes) < target_count, "Should have reduced count on failure"

class TestRelationDerivation:
    """Test that derived relations match geometric reality."""

    def test_derive_relations_consistency(self):
        """Verify derived relations are geometrically consistent."""
        # Create known boxes
        boxes = [
            {'id': 1, 'x': 10, 'y': 10, 'w': 20, 'h': 20},  # Left
            {'id': 2, 'x': 50, 'y': 10, 'w': 20, 'h': 20}   # Right
        ]

        relations = derive_all_relations(boxes)

        # Box 1 should be "left of" Box 2
        relations_text = " ".join(relations)
        assert "left of" in relations_text.lower(), "Expected 'left of' relation"

    def test_derive_relations_vertical(self):
        """Verify vertical relations are derived correctly."""
        boxes = [
            {'id': 1, 'x': 10, 'y': 10, 'w': 20, 'h': 20},  # Top
            {'id': 2, 'x': 10, 'y': 50, 'w': 20, 'h': 20}   # Bottom
        ]

        relations = derive_all_relations(boxes)
        relations_text = " ".join(relations)
        assert "above" in relations_text.lower() or "below" in relations_text.lower(), \
            "Expected vertical relation"

class TestSchemaCompliance:
    """Test that generated data complies with schema."""

    def test_annotation_structure(self):
        """Verify annotation data has required fields."""
        from synthetic.validator import validate_synthetic_image_file

        # Mock data
        annotation = {
            'image_path': 'test.png',
            'bounding_boxes': [
                {'id': 1, 'x': 10, 'y': 10, 'w': 20, 'h': 20}
            ],
            'derived_relations': ['left of'],
            'region_count': 25
        }

        # This should not raise
        assert validate_synthetic_image_file(annotation) is True

class TestIntegration:
    """Integration tests for the generator pipeline."""

    @patch('synthetic.generator.fetch_dataset_sample')
    @patch('synthetic.generator.serialize_synthetic_sample')
    def test_pipeline_execution(self, mock_serialize, mock_fetch):
        """Test pipeline runs without crashing on mock data."""
        # Mock dataset
        mock_dataset = [
            {
                'image': MagicMock(size=(800, 600)),
                'annotations': []
            }
        ]
        mock_fetch.return_value = mock_dataset
        mock_serialize.return_value = Path('/tmp/test.png')

        # Run for a single bin
        stats = generate_sample_for_bin(
            bin_count=25,
            source_dataset=mock_dataset,
            output_dir=Path('/tmp'),
            start_idx=0
        )

        assert 'attempted' in stats
        assert 'successful' in stats
        assert 'failed' in stats

if __name__ == "__main__":
    pytest.main([__file__, "-v"])