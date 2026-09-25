"""
Deterministic Rule-Based Visual Detector (T026a Implementation).

This module implements the strict visual threshold detector required for
SC-005 (Nested Model Comparison) and baseline F1 calculation.

Unlike the NoisyVisualDetector, this implementation applies NO label flip noise
and NO temporal jitter. It strictly enforces visual rules based on object
position, velocity, and confidence.
"""
import math
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

@dataclass
class DeterministicPrediction:
    label: str  # 'critical' or 'silence'
    confidence: float
    reason: str
    metadata: Dict[str, Any]

class DeterministicVisualDetector:
    """
    Strict rule-based detector for visual events.
    
    Rules:
    1. Critical: Person bounding box center Y > 0.7 (near bottom of frame) 
       AND velocity > threshold (falling motion) OR static on ground.
    2. Silence: Person present but not in critical state.
    3. No Person: Silence.
    """
    
    # Configuration constants (tuned for synthetic data scale)
    GROUND_THRESHOLD_Y = 0.70  # Y-coordinate threshold for "on ground"
    VELOCITY_THRESHOLD = 0.15  # Minimum Y-velocity to consider "falling"
    CONFIDENCE_MIN = 0.50      # Minimum object detection confidence
    
    def __init__(self):
        self.logger_name = "DeterministicDetector"

    def _calculate_velocity(self, current_frame: Dict[str, Any], prev_frame: Optional[Dict[str, Any]]) -> float:
        """
        Calculates the vertical velocity of the person's bounding box center.
        Returns a normalized velocity value (0.0 to 1.0).
        """
        if not prev_frame or "objects" not in prev_frame or "objects" not in current_frame:
            return 0.0
        
        if not prev_frame["objects"] or not current_frame["objects"]:
            return 0.0

        # Assume we track the largest object (person)
        # In synthetic data, usually only one person per frame
        curr_obj = current_frame["objects"][0]
        prev_obj = prev_frame["objects"][0]

        curr_y = curr_obj["bbox"][1] + (curr_obj["bbox"][3] / 2) # Center Y
        prev_y = prev_obj["bbox"][1] + (prev_obj["bbox"][3] / 2)

        # Delta Y
        dy = curr_y - prev_y
        
        # Normalize by frame height (assuming normalized coords 0-1)
        # If coords are absolute, we'd need frame height, but synthetic data uses normalized
        return abs(dy)

    def detect(self, frame: Dict[str, Any]) -> DeterministicPrediction:
        """
        Analyzes a single frame and returns a deterministic prediction.
        """
        # 1. Check for person presence
        objects = frame.get("objects", [])
        
        if not objects:
            return DeterministicPrediction(
                label="silence",
                confidence=1.0,
                reason="No person detected",
                metadata={"objects_count": 0}
            )

        # Filter by confidence
        valid_objects = [o for o in objects if o.get("confidence", 0) >= self.CONFIDENCE_MIN]
        
        if not valid_objects:
            return DeterministicPrediction(
                label="silence",
                confidence=1.0,
                reason="No person with sufficient confidence",
                metadata={"objects_count": len(objects), "filtered": len(valid_objects)}
            )

        # Assume first valid object is the target person
        person = valid_objects[0]
        bbox = person["bbox"] # [x, y, w, h] normalized 0-1
        
        # Calculate center Y
        center_y = bbox[1] + (bbox[3] / 2)
        
        # 2. Determine state based on position
        is_on_ground = center_y >= self.GROUND_THRESHOLD_Y

        # 3. Check velocity (if previous frame context is available in metadata)
        # Note: For single-frame processing, we rely on position.
        # If velocity data is pre-computed in frame metadata, use it.
        velocity = frame.get("metadata", {}).get("velocity_y", 0.0)
        
        is_falling = velocity > self.VELOCITY_THRESHOLD

        # 4. Apply Strict Rules
        if is_on_ground or is_falling:
            reason = "Critical: Person on ground" if is_on_ground else "Critical: Falling motion detected"
            return DeterministicPrediction(
                label="critical",
                confidence=0.95, # High confidence for deterministic rules
                reason=reason,
                metadata={
                    "center_y": center_y,
                    "velocity": velocity,
                    "rule_triggered": "ground" if is_on_ground else "velocity"
                }
            )
        else:
            return DeterministicPrediction(
                label="silence",
                confidence=0.90,
                reason="Person active, not on ground",
                metadata={
                    "center_y": center_y,
                    "velocity": velocity
                }
            )

def load_raw_frames(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Helper to load all frames from raw directory for batch processing if needed.
    Returns a list of frame dictionaries.
    """
    frames = []
    if not raw_dir.exists():
        return frames
    
    for file_path in sorted(raw_dir.glob("*.jsonl")):
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    frames.append(json.loads(line))
    return frames

def main():
    """
    Entry point for direct execution (though run_deterministic_detector.py is preferred).
    """
    print("Deterministic Detector Module Loaded.")
    print("Use src/baseline/run_deterministic_detector.py to execute the pipeline.")

if __name__ == "__main__":
    main()
