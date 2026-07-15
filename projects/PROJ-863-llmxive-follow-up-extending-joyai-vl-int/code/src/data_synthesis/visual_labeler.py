"""
Visual Labeler Module for JoyAI-VL-Interaction Synthetic Data.

This module implements the labeling logic for synthetic video frames using
object detection (YOLOv8 with COCO classes) to distinguish between
"critical" events (falls, accidents) and "silence" (normal activity).

CRITICAL CONSTRAINT: Labeling relies SOLELY on visual content. No VLM
API calls or internal state analysis are performed in this module.
"""

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    import cv2
    import numpy as np
except ImportError:
    raise ImportError(
        "Required packages 'opencv-python' and 'numpy' are missing. "
        "Install them via: pip install opencv-python numpy"
    )

# Attempt to import ultralytics for YOLOv8
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from src.utils.logging import get_logger
from src.utils.env_config import load_environment_config

# Define COCO classes that represent "critical" events
# Based on common safety monitoring scenarios:
# - Person (0): Needed to detect falls
CRITICAL_CLASSES = {
    0: "person",  # Required for fall detection logic
    # Add other specific critical objects if needed (e.g., fire, car in specific contexts)
    # For this implementation, we rely on 'person' state analysis
}

# Thresholds for fall detection (simplified rule-based on YOLO output)
FALL_HEIGHT_THRESHOLD = 0.3  # Relative height drop threshold
FALL_VELOCITY_THRESHOLD = 0.5  # Relative velocity threshold

logger = get_logger(__name__)


@dataclass
class FrameLabel:
    """Data structure for a labeled video frame."""
    frame_id: str
    timestamp: float
    label: str  # "critical" or "silence"
    confidence: float
    detection_details: Dict[str, Any]
    metadata: Dict[str, Any]


class VisualLabeler:
    """
    Labels video frames using object detection and rule-based logic.

    This class processes video streams or individual frames to generate
    ground-truth labels based purely on visual evidence.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the Visual Labeler.

        Args:
            model_path: Path to the YOLO model weights. If None, attempts
                        to load 'yolov8n.pt' from cache or fails if unavailable.
        """
        self.model_path = model_path or os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
        self.model = None
        self._init_model()

    def _init_model(self) -> None:
        """Load the YOLO model."""
        if not YOLO_AVAILABLE:
            raise RuntimeError(
                "Ultralytics library is required for object detection. "
                "Install it via: pip install ultralytics"
            )

        logger.info(f"Loading YOLO model from: {self.model_path}")
        try:
            self.model = YOLO(self.model_path)
            logger.info("YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run object detection on a single frame.

        Args:
            frame: OpenCV BGR image array.

        Returns:
            List of detection dictionaries containing class, bbox, confidence.
        """
        if self.model is None:
            raise RuntimeError("Model not initialized.")

        results = self.model(frame, verbose=False)
        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                box = boxes[i]
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                # Only process relevant classes
                if cls_id in CRITICAL_CLASSES:
                    detections.append({
                        "class_id": cls_id,
                        "class_name": CRITICAL_CLASSES[cls_id],
                        "confidence": conf,
                        "bbox": bbox
                    })

        return detections

    def _analyze_person_state(self, detections: List[Dict[str, Any]], 
                              frame_height: int, frame_width: int) -> Tuple[str, float, Dict]:
        """
        Analyze person detections to determine if a fall occurred.

        This is a simplified rule-based detector:
        - If a person's bounding box aspect ratio is inverted (taller than wide)
          and they are low in the frame, it might be a fall.
        - For a more robust implementation, temporal tracking would be needed.
          Here we use a static heuristic for the synthetic generator context.

        Returns:
            (label, confidence, details)
        """
        if not detections:
            return "silence", 1.0, {"reason": "no_person_detected"}

        # Filter for person detections
        person_dets = [d for d in detections if d["class_name"] == "person"]
        
        if not person_dets:
            return "silence", 1.0, {"reason": "no_person_detected"}

        # Simple heuristic: Check if the person is "lying down" (wide box, low y)
        # or "standing" (tall box).
        # For synthetic data, we assume the generator creates distinct patterns.
        # We will flag "critical" if the box is wide relative to height and low in frame.
        
        # Use the most confident detection
        best_det = max(person_dets, key=lambda x: x["confidence"])
        x1, y1, x2, y2 = best_det["bbox"]
        
        width = x2 - x1
        height = y2 - y1
        center_y = y1 + height / 2

        aspect_ratio = width / max(height, 1e-5)
        
        # Heuristic for "Fall" (Critical):
        # 1. Person is wide (aspect ratio > 1.5)
        # 2. Person is in the lower half of the frame (center_y > 0.5 * frame_height)
        
        is_fall_candidate = (aspect_ratio > 1.5) and (center_y > 0.5 * frame_height)

        if is_fall_candidate:
            return "critical", best_det["confidence"] * 0.9, {
                "reason": "fall_heuristic",
                "aspect_ratio": aspect_ratio,
                "center_y_ratio": center_y / frame_height
            }
        
        return "silence", best_det["confidence"] * 0.9, {
            "reason": "normal_posture",
            "aspect_ratio": aspect_ratio
        }

    def label_frame(self, frame: np.ndarray, frame_id: str, timestamp: float) -> FrameLabel:
        """
        Process a single frame and return a labeled result.

        Args:
            frame: OpenCV BGR image.
            frame_id: Unique identifier for the frame.
            timestamp: Timestamp in seconds.

        Returns:
            FrameLabel object.
        """
        detections = self.detect_objects(frame)
        label, confidence, details = self._analyze_person_state(
            detections, frame.shape[0], frame.shape[1]
        )

        return FrameLabel(
            frame_id=frame_id,
            timestamp=timestamp,
            label=label,
            confidence=confidence,
            detection_details=detections,
            metadata={"detection_count": len(detections)}
        )

    def label_video_stream(self, video_path: str, output_path: str) -> None:
        """
        Process a video file and write labels to a JSONL file.

        Args:
            video_path: Path to the input video file.
            output_path: Path to the output JSONL file.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Processing video: {video_path} ({total_frames} frames)")

        with open(output_path, 'w') as f:
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp = frame_idx / fps
                label_obj = self.label_frame(frame, f"frame_{frame_idx:06d}", timestamp)
                
                # Write JSONL
                f.write(json.dumps(asdict(label_obj)) + '\n')
                
                frame_idx += 1
                if frame_idx % 100 == 0:
                    logger.debug(f"Processed {frame_idx}/{total_frames} frames")

        cap.release()
        logger.info(f"Labeling complete. Output written to: {output_path}")


def main():
    """
    CLI entry point for the visual labeler.
    
    Usage:
      python -m src.data_synthesis.visual_labeler --input <video.mp4> --output <labels.jsonl>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Label video frames using visual detection.")
    parser.add_argument("--input", type=str, required=True, help="Input video path")
    parser.add_argument("--output", type=str, required=True, help="Output JSONL path")
    parser.add_argument("--model", type=str, default=None, help="YOLO model path")
    
    args = parser.parse_args()

    # Setup environment
    load_environment_config()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Initialize and run
    labeler = VisualLabeler(model_path=args.model)
    labeler.label_video_stream(args.input, args.output)

    logger.info("Visual labeling task finished.")


if __name__ == "__main__":
    main()
