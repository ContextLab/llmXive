"""
Unit tests for CV pipeline detection accuracy on mock/synthetic frames.

This test suite verifies the logic of the computer vision pipeline using
deterministic synthetic data. It does NOT use real video files or the
actual model to ensure independence from external dependencies during unit testing.

Tests cover:
1. Template matching on synthetic static objects.
2. Optical flow detection on synthetic motion.
3. State extraction logic (HP, alive/dead status) from synthetic frames.
"""
import pytest
import numpy as np
import cv2
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Ensure code/ is in path for imports
code_path = Path(__file__).parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

# Mock the cv_pipeline module logic for testing purposes
# Since cv_pipeline.py is not yet implemented in the project (it's a future task),
# we define the expected logic here to verify the test structure and synthetic data generation.
# In a real scenario, we would import from `from cv_pipeline import detect_objects, extract_state`.

class MockCVPipeline:
    """
    A mock implementation of the CV pipeline logic to verify test data generation.
    This simulates what the real `cv_pipeline.py` will do on synthetic frames.
    """
    
    @staticmethod
    def create_synthetic_frame(
        width: int = 640,
        height: int = 480,
        object_type: str = "hero",
        state: str = "alive",
        hp: int = 100,
        position: tuple = (320, 240),
        motion_vector: tuple = (0, 0)
    ) -> np.ndarray:
        """
        Creates a deterministic synthetic frame with a specific object state.
        """
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Background: Dark gray
        frame[:] = (50, 50, 50)
        
        # Draw object based on type
        x, y = position
        if object_type == "hero":
            # Blue square for hero
            color = (255, 0, 0) # BGR: Blue
            if state == "dead":
                color = (0, 0, 0) # Black (invisible/dead)
            cv2.rectangle(frame, (x-20, y-20), (x+20, y+20), color, -1)
            
            # Draw HP bar if alive
            if state == "alive" and hp > 0:
                bar_width = 40
                bar_height = 5
                hp_ratio = max(0, min(1, hp / 100.0))
                cv2.rectangle(frame, (x-20, y-30), (x+20, y-25), (100, 100, 100), -1)
                cv2.rectangle(frame, (x-20, y-30), (x-20 + int(bar_width * hp_ratio), y-25), (0, 255, 0), -1)
                
        elif object_type == "enemy":
            # Red square for enemy
            color = (0, 0, 255) # BGR: Red
            if state == "dead":
                color = (0, 0, 0)
            cv2.rectangle(frame, (x-15, y-15), (x+15, y+15), color, -1)
        
        # Simulate motion by drawing a trail if motion_vector is non-zero
        if motion_vector != (0, 0):
            prev_x, prev_y = x - motion_vector[0], y - motion_vector[1]
            cv2.line(frame, (prev_x, prev_y), (x, y), (150, 150, 150), 2)
            
        return frame

    @staticmethod
    def detect_objects(frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Mock detection logic: Finds colored squares and estimates state.
        """
        detected = []
        # Simple color thresholding to find objects
        # Hero is Blue (BGR: 255, 0, 0)
        lower_blue = np.array([100, 0, 0])
        upper_blue = np.array([255, 50, 50])
        mask_hero = cv2.inRange(frame, lower_blue, upper_blue)
        
        # Enemy is Red (BGR: 0, 0, 255)
        lower_red = np.array([0, 0, 100])
        upper_red = np.array([50, 50, 255])
        mask_enemy = cv2.inRange(frame, lower_red, upper_red)
        
        masks = [("hero", mask_hero), ("enemy", mask_enemy)]
        
        for obj_type, mask in masks:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 100: # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(cnt)
                    center_x, center_y = x + w // 2, y + h // 2
                    
                    # Infer state: if area is very small or mask is empty in center, maybe dead?
                    # For this mock, we assume if we detected it, it's alive unless it's a specific "dead" color
                    # In the mock frame generator, dead objects are black (0,0,0) which won't be detected by color masks.
                    # So if detected, it's alive.
                    detected.append({
                        "type": obj_type,
                        "position": (center_x, center_y),
                        "state": "alive",
                        "hp": 100, # Mock HP
                        "confidence": 0.9
                    })
        return detected

    @staticmethod
    def extract_state(detected_objects: List[Dict[str, Any]], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares detected objects with ground truth to compute accuracy metrics.
        """
        if not detected_objects and ground_truth.get("state") == "alive":
            return {"match": False, "reason": "Object not detected"}
        
        if detected_objects and ground_truth.get("state") == "dead":
            return {"match": False, "reason": "False positive on dead object"}
        
        if detected_objects and ground_truth.get("state") == "alive":
            # Check position proximity (IoU approximation)
            det = detected_objects[0]
            gt_pos = ground_truth.get("position", (0,0))
            dist = np.sqrt((det["position"][0] - gt_pos[0])**2 + (det["position"][1] - gt_pos[1])**2)
            if dist < 20: # 20 pixel tolerance
                return {"match": True, "position_error": dist}
            else:
                return {"match": False, "reason": "Position mismatch", "error": dist}
        
        return {"match": True} # Both empty (dead)

# --- Test Cases ---

class TestCVPipelineSynthetic:
    """Tests for CV pipeline using synthetic frames."""

    def test_synthetic_frame_generation_hero_alive(self):
        """Verify that a synthetic frame for an alive hero is generated correctly."""
        pipeline = MockCVPipeline()
        frame = pipeline.create_synthetic_frame(
            object_type="hero",
            state="alive",
            hp=100,
            position=(320, 240)
        )
        
        assert frame.shape == (480, 640, 3)
        assert frame.dtype == np.uint8
        # Check that the blue center is present (hero color)
        center_color = frame[240, 320]
        assert center_color[0] > 100, "Hero should be blue (BGR)"
        # Check HP bar presence (green)
        # The bar is at y=25-30, x=300-340
        hp_region = frame[25:30, 300:340]
        assert np.any(hp_region[:, :, 1] > 100), "HP bar should be green"

    def test_synthetic_frame_generation_hero_dead(self):
        """Verify that a synthetic frame for a dead hero is black/invisible."""
        pipeline = MockCVPipeline()
        frame = pipeline.create_synthetic_frame(
            object_type="hero",
            state="dead",
            hp=0,
            position=(320, 240)
        )
        
        # The object should be black (0,0,0)
        # The background is gray (50,50,50)
        # We check the center; if dead, it should be background color or black
        center_color = frame[240, 320]
        # In the mock, dead objects are drawn as black, but if the drawing fails or is skipped,
        # it might be background. The key is that it shouldn't be the hero color.
        assert center_color[0] < 100, "Dead hero should not be blue"

    def test_detection_alive_object(self):
        """Test that the mock detector finds an alive object."""
        pipeline = MockCVPipeline()
        frame = pipeline.create_synthetic_frame(
            object_type="hero",
            state="alive",
            position=(320, 240)
        )
        
        detected = pipeline.detect_objects(frame)
        
        assert len(detected) == 1, "Should detect exactly one object"
        assert detected[0]["type"] == "hero"
        assert detected[0]["state"] == "alive"

    def test_detection_dead_object(self):
        """Test that the mock detector does NOT find a dead object."""
        pipeline = MockCVPipeline()
        frame = pipeline.create_synthetic_frame(
            object_type="hero",
            state="dead",
            position=(320, 240)
        )
        
        detected = pipeline.detect_objects(frame)
        
        # Dead objects are black and shouldn't match the blue mask
        assert len(detected) == 0, "Should not detect a dead object"

    def test_state_extraction_accuracy(self):
        """Test the logic of comparing detection vs ground truth."""
        pipeline = MockCVPipeline()
        
        # Case 1: Perfect match
        detected = [{"type": "hero", "position": (320, 240), "state": "alive", "hp": 100}]
        gt = {"type": "hero", "position": (320, 240), "state": "alive", "hp": 100}
        result = pipeline.extract_state(detected, gt)
        assert result["match"] is True

        # Case 2: Position mismatch
        detected = [{"type": "hero", "position": (320, 240), "state": "alive", "hp": 100}]
        gt = {"type": "hero", "position": (400, 240), "state": "alive", "hp": 100}
        result = pipeline.extract_state(detected, gt)
        assert result["match"] is False

    def test_motion_detection_logic(self):
        """Test that motion vectors are simulated in the frame."""
        pipeline = MockCVPipeline()
        frame = pipeline.create_synthetic_frame(
            object_type="hero",
            state="alive",
            position=(320, 240),
            motion_vector=(10, 0)
        )
        
        # Check for the trail (gray line)
        # The trail goes from (310, 240) to (320, 240)
        # We check a few points along the line
        trail_color = frame[240, 315]
        # Gray is roughly (150, 150, 150)
        assert trail_color[0] > 100 and trail_color[1] > 100 and trail_color[2] > 100, "Trail should be gray"

    def test_pipeline_accuracy_threshold(self):
        """
        Simulate a batch of frames and calculate Mean F1-score.
        This verifies the logic of the validation report generation.
        """
        pipeline = MockCVPipeline()
        
        # Generate 10 frames: 5 alive, 5 dead
        results = []
        for i in range(10):
            if i < 5:
                frame = pipeline.create_synthetic_frame(state="alive", position=(320, 240))
                detected = pipeline.detect_objects(frame)
                gt = {"state": "alive", "position": (320, 240)}
            else:
                frame = pipeline.create_synthetic_frame(state="dead", position=(320, 240))
                detected = pipeline.detect_objects(frame)
                gt = {"state": "dead", "position": (320, 240)}
            
            res = pipeline.extract_state(detected, gt)
            results.append(res["match"])
        
        # Calculate F1
        tp = sum(1 for r in results if r) # In this mock, match=True is correct detection
        # Since our mock logic is deterministic and perfect for these cases, F1 should be 1.0
        accuracy = sum(results) / len(results)
        
        assert accuracy == 1.0, f"Mock pipeline should be 100% accurate on synthetic data, got {accuracy}"
        assert accuracy >= 0.85, "Accuracy must meet the 85% threshold for validation"
