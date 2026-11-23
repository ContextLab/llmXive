"""
Visual Labeler Module for JoyAI-VL Interaction Project.

Implements object detection-based labeling of video frames to distinguish
between 'critical' events (falls, collisions) and 'silence' (normal activity).
Uses YOLOv8 with COCO classes to ensure strictly visual labeling without VLM calls.
"""
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import cv2
import numpy as np

# Lazy import of ultralytics to avoid hard dependency if not needed for testing
# but required for execution.
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from src.utils.logging import get_logger, log_no_vlm_call
from src.utils.validation import validate_dataclass_instance

# Critical COCO class IDs that indicate a 'critical' event
# Based on COCO dataset: 1=person, 2=bicycle, 3=car, 4=motorcycle, 5=airplane, 
# 6=bus, 7=train, 8=truck, 9=boat, 10=traffic light, 11=fire hydrant, 
# 12=stop sign, 13=parking meter, 14=bench, 15=bird, 16=cat, 17=dog, 
# 18=horse, 19=sheep, 20=cow, 21=elephant, 22=bear, 23=zebra, 24=giraffe, 
# 25=backpack, 26=umbrella, 27=handbag, 28=tie, 29=suitcase, 30=frisbee, 
# 31=snowboards, 32=sports ball, 33=kite, 34=baseball bat, 35=baseball glove, 
# 36=skateboard, 37=surfboard, 38=tennis racket, 39=bottle, 40=wine glass, 
# 41=cup, 42=fork, 43=knife, 44=spoon, 45=bowl, 46=banana, 47=apple, 
# 48=sandwich, 49=orange, 50=broccoli, 51=carrot, 52=hot dog, 53=pizza, 
# 54=donut, 55=cake, 56=chair, 57=couch, 58=potted plant, 59=bed, 
# 60=dining table, 61=toilet, 62=tv, 63=laptop, 64=mouse, 65=remote, 
# 66=keyboard, 67=cell phone, 68=microwave, 69=oven, 70=toaster, 
# 71=sink, 72=refrigerator, 73=book, 74=clock, 75=vase, 76=scissors, 
# 77=teddy bear, 78=hair drier, 79=toothbrush
# 
# For 'fall' detection, we primarily look for 'person' (ID 0 in COCO index 1)
# and potentially 'bed' (ID 59) or 'chair' (ID 56) if a person is near them in a fall context.
# However, the task specifies "critical" vs "silence". 
# We define 'critical' as: Person detected with high confidence AND (falling motion or near ground).
# Since simple object detection doesn't give motion, we use a heuristic:
# If a 'person' is detected and their bounding box is in the lower 20% of the frame, 
# it's likely a fall or collapse.
# 
# Simplified Rule for this task:
# Critical: Person detected (COCO ID 0) with confidence > 0.5 AND y_center > 0.8 (lower part of image)
# OR: Multiple people detected in a small area (crowd crush risk) - optional.
# For now, we focus on the 'person on ground' heuristic.

CRITICAL_CLASSES = [0]  # Person (COCO index 0)
CONFIDENCE_THRESHOLD = 0.5
GROUND_THRESHOLD = 0.8  # y_center > 80% of image height indicates being on the ground

@dataclass
class FrameLabel:
    """Data structure for a labeled video frame."""
    frame_id: str
    timestamp: float
    label: str  # 'critical' or 'silence'
    confidence: float
    detected_objects: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        validate_dataclass_instance(self)

class VisualLabeler:
    """
    Labels video frames using object detection (YOLO) to identify critical events.
    Ensures zero VLM calls by relying solely on visual features.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        Initialize the VisualLabeler.
        
        Args:
            model_path: Path to YOLO model weights. If None, uses default 'yolov8n.pt'.
            device: Device to run inference on ('cpu' or 'cuda').
        """
        self.logger = get_logger(__name__)
        self.device = device
        
        if not YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics package is required for VisualLabeler. "
                "Install it via: pip install ultralytics"
            )
        
        if model_path is None:
            model_path = "yolov8n.pt"  # Default nano model for speed
        
        self.logger.info(f"Loading YOLO model from {model_path} on {device}")
        self.model = YOLO(model_path)
        self.model.to(device)
        self.logger.info("YOLO model loaded successfully")
        
        # Log that no VLM is used
        log_no_vlm_call("visual_labeler", "Using YOLO object detection instead of VLM")

    def _detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run object detection on a single frame.
        
        Args:
            frame: OpenCV BGR image (numpy array).
            
        Returns:
            List of detected objects with class, confidence, and bbox.
        """
        results = self.model(frame, verbose=False)
        detections = []
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                boxes = result.boxes
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i].item())
                    conf = float(boxes.conf[i].item())
                    x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                    h, w = frame.shape[:2]
                    
                    detections.append({
                        "class_id": cls_id,
                        "class_name": result.names[cls_id],
                        "confidence": conf,
                        "bbox": [x1, y1, x2, y2],
                        "center_x": (x1 + x2) / 2,
                        "center_y": (y1 + y2) / 2
                    })
        
        return detections

    def _classify_frame(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> Tuple[str, float]:
        """
        Classify a frame as 'critical' or 'silence' based on detections.
        
        Logic:
        - If a 'person' (class 0) is detected with confidence > threshold
          AND their center_y is in the lower 20% of the frame (indicating they are on the ground),
          classify as 'critical'.
        - Otherwise, 'silence'.
        
        Args:
            frame: The image frame (for dimensions).
            detections: List of detected objects.
            
        Returns:
            Tuple of (label, max_confidence)
        """
        h, w = frame.shape[:2]
        critical_detected = False
        max_conf = 0.0

        for det in detections:
            if det["class_id"] in CRITICAL_CLASSES and det["confidence"] >= CONFIDENCE_THRESHOLD:
                max_conf = max(max_conf, det["confidence"])
                # Check if person is on the ground (y_center > 80% of height)
                if det["center_y"] > (h * GROUND_THRESHOLD):
                    critical_detected = True
                    break
        
        label = "critical" if critical_detected else "silence"
        confidence = max_conf if critical_detected else 1.0 - max_conf # Inverse for silence confidence logic if needed, but we just return max_conf
        
        # For simplicity, return the confidence of the critical detection if critical, else 0.0
        if label == "critical":
            return label, max_conf
        else:
            return label, 0.0

    def label_frame(self, frame: np.ndarray, frame_id: str, timestamp: float) -> FrameLabel:
        """
        Label a single frame.
        
        Args:
            frame: OpenCV BGR image.
            frame_id: Unique identifier for the frame.
            timestamp: Timestamp of the frame in seconds.
            
        Returns:
            FrameLabel dataclass instance.
        """
        detections = self._detect_objects(frame)
        label, confidence = self._classify_frame(frame, detections)
        
        frame_label = FrameLabel(
            frame_id=frame_id,
            timestamp=timestamp,
            label=label,
            confidence=confidence,
            detected_objects=detections,
            metadata={"frame_shape": frame.shape, "detection_count": len(detections)}
        )
        
        return frame_label

    def label_video_stream(self, input_path: str, output_path: str, chunk_size: int = 100):
        """
        Process a video stream (or directory of frames) and write labels to JSONL.
        
        Args:
            input_path: Path to video file or directory of frames.
            output_path: Path to output JSONL file.
            chunk_size: Number of frames to process before writing to disk (streaming).
        """
        self.logger.info(f"Starting visual labeling for {input_path} -> {output_path}")
        
        # Check if input is a video file or directory
        if os.path.isfile(input_path) and input_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            is_video = True
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise RuntimeError(f"Could not open video file: {input_path}")
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
        elif os.path.isdir(input_path):
            is_video = False
            # Assume frames are named sequentially or we just iterate
            frame_files = sorted([f for f in os.listdir(input_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            if not frame_files:
                raise RuntimeError(f"No image files found in directory: {input_path}")
            frame_count = len(frame_files)
            fps = 30.0 # Default assumption for image sequences
            self.logger.info(f"Detected {frame_count} frames in directory")
        else:
            raise ValueError(f"Input path must be a video file or image directory: {input_path}")

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        labels_written = 0
        start_time = time.time()

        try:
            with open(output_path, 'w') as f:
                frame_idx = 0
                while True:
                    if is_video:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        timestamp = frame_idx / fps
                    else:
                        img_path = os.path.join(input_path, frame_files[frame_idx])
                        frame = cv2.imread(img_path)
                        if frame is None:
                            frame_idx += 1
                            continue
                        timestamp = frame_idx / fps
                    
                    frame_id = f"frame_{frame_idx:06d}"
                    label_obj = self.label_frame(frame, frame_id, timestamp)
                    
                    # Write to JSONL
                    f.write(json.dumps(asdict(label_obj)) + '\n')
                    labels_written += 1
                    
                    # Stream flush periodically
                    if labels_written % chunk_size == 0:
                        f.flush()
                    
                    frame_idx += 1
                    
                    # Progress logging
                    if frame_idx % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = frame_idx / elapsed if elapsed > 0 else 0
                        self.logger.info(f"Processed {frame_idx}/{frame_count} frames ({rate:.1f} fps)")

        finally:
            if is_video:
                cap.release()
        
        total_time = time.time() - start_time
        self.logger.info(f"Labeling complete. Wrote {labels_written} labels in {total_time:.2f}s.")
        log_no_vlm_call("visual_labeler", f"Processed {labels_written} frames without VLM calls")

    def label_directory(self, input_dir: str, output_dir: str):
        """
        Process a directory of video files or frame directories.
        
        Args:
            input_dir: Directory containing input videos/frames.
            output_dir: Directory to write JSONL outputs.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        items = os.listdir(input_dir)
        processed = 0
        for item in items:
            item_path = os.path.join(input_dir, item)
            if os.path.isfile(item_path) and item.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                output_file = os.path.join(output_dir, f"{os.path.splitext(item)[0]}.jsonl")
                self.label_video_stream(item_path, output_file)
                processed += 1
            elif os.path.isdir(item_path):
                # Treat as a sequence of frames
                output_file = os.path.join(output_dir, f"{item}_labels.jsonl")
                self.label_video_stream(item_path, output_file)
                processed += 1
        
        self.logger.info(f"Completed labeling {processed} items in {input_dir}")

def main():
    """
    Entry point for running the visual labeler from command line.
    Usage: python -m src.data_synthesis.visual_labeler --input <path> --output <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Label video frames using YOLO object detection")
    parser.add_argument("--input", type=str, required=True, help="Input video file or directory of frames")
    parser.add_argument("--output", type=str, required=True, help="Output JSONL file or directory")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="YOLO model path")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    
    args = parser.parse_args()
    
    labeler = VisualLabeler(model_path=args.model, device=args.device)
    
    if os.path.isfile(args.input) and args.input.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        labeler.label_video_stream(args.input, args.output)
    elif os.path.isdir(args.input):
        # If output is a file, we can't handle multiple inputs. 
        # If output is a dir, we process all items.
        if os.path.isdir(args.output):
            labeler.label_directory(args.input, args.output)
        else:
            # Assume single directory input -> single output file
            labeler.label_video_stream(args.input, args.output)
    else:
        raise ValueError(f"Invalid input path: {args.input}")

if __name__ == "__main__":
    main()
