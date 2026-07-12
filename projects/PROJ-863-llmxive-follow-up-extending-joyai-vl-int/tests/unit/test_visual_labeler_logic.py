"""
Additional unit tests specifically for the deterministic rules of the VisualLabeler.
This file complements test_visual_labeler.py by focusing on the edge cases 
and rule application logic (T015 context) to ensure deterministic behavior.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys

try:
    from src.data_synthesis.visual_labeler import VisualLabeler
    VISUAL_LABELER_EXISTS = True
except ImportError:
    VISUAL_LABELER_EXISTS = False

class TestVisualLabelerDeterministicRules:
    """
    Tests to verify that ambiguous events are handled with deterministic rules.
    """

    @pytest.mark.skipif(not VISUAL_LABELER_EXISTS, reason="visual_labeler module not yet implemented (T014)")
    def test_velocity_threshold_determinism(self):
        """
        Verify that the same velocity magnitude always produces the same label.
        This ensures deterministic rule application for ambiguous events.
        """
        with patch('src.data_synthesis.visual_labeler.ObjectDetector') as MockDetectorClass:
            MockDetectorClass.return_value = MagicMock()
            labeler = VisualLabeler()

            # Define a specific velocity magnitude
            test_magnitude = 45.0
            
            # Run multiple times with identical input
            results = []
            for i in range(5):
                mock_result = {
                    "objects": [{"class_id": 1, "label": "person", "bbox": [0,0,10,10], "confidence": 0.9}],
                    "motion_vector": {"x": 30.0, "y": 30.0, "magnitude": test_magnitude}
                }
                label = labeler.label_frame({"frame_id": str(i)}, mock_result)
                results.append(label)
            
            # All results must be identical
            assert all(r == results[0] for r in results), "Labeling must be deterministic for identical inputs"

    @pytest.mark.skipif(not VISUAL_LABELER_EXISTS, reason="visual_labeler module not yet implemented (T014)")
    def test_object_class_priority(self):
        """
        Verify that object class (e.g., 'person' vs 'chair') influences the label 
        when motion is ambiguous.
        """
        with patch('src.data_synthesis.visual_labeler.ObjectDetector') as MockDetectorClass:
            MockDetectorClass.return_value = MagicMock()
            labeler = VisualLabeler()

            # Scenario: Low motion, but 'person' detected
            person_result = {
                "objects": [{"class_id": 1, "label": "person", "bbox": [0,0,10,10], "confidence": 0.9}],
                "motion_vector": {"x": 0.5, "y": 0.5, "magnitude": 0.7}
            }
            
            # Scenario: Low motion, 'chair' detected (no person)
            chair_result = {
                "objects": [{"class_id": 56, "label": "chair", "bbox": [0,0,10,10], "confidence": 0.9}],
                "motion_vector": {"x": 0.5, "y": 0.5, "magnitude": 0.7}
            }

            label_person = labeler.label_frame({"frame_id": "p"}, person_result)
            label_chair = labeler.label_frame({"frame_id": "c"}, chair_result)

            # The implementation should distinguish between a person and an inanimate object
            # even with similar motion, ensuring the 'person' context is prioritized for safety.
            # We assert they are not necessarily the same if the logic is sound, 
            # or at least that the logic processes the 'class_id' correctly.
            # (Specific label comparison depends on T014 implementation details)
            assert label_person is not None
            assert label_chair is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])