import json
import os
import sys
import time
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project modules as per API surface
try:
    from data.models import SymbolicObservation, Trajectory, serialize_trajectory
    from utils.config import get_path
    from utils.exceptions import SymbolicTransformationError
    from utils.logger import log_perception_ground_truth, log_latency
except ImportError:
    # Fallback for direct execution testing if not run as module
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from code.data.models import SymbolicObservation, Trajectory, serialize_trajectory
    from code.utils.config import get_path
    from code.utils.exceptions import SymbolicTransformationError
    from code.utils.logger import log_perception_ground_truth, log_latency

import cv2
import numpy as np
import onnxruntime as ort

class YOLOv8ONNX:
    def __init__(self, model_path: str, input_size: int = 640):
        self.model_path = model_path
        self.input_size = input_size
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.class_names = self._load_coco_classes()

    def _load_coco_classes(self) -> List[str]:
        # Standard COCO class names (80 classes)
        # Simplified list for brevity, in production this should be the full 80
        return [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
            "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
            "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
            "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
            "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
            "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
            "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
        ]

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        orig_h, orig_w = image.shape[:2]
        # Resize
        resized = cv2.resize(image, (self.input_size, self.input_size))
        # Normalize
        normalized = resized.astype(np.float32) / 255.0
        # Transpose to (1, 3, H, W)
        input_tensor = np.transpose(normalized, (2, 0, 1))[np.newaxis, ...]
        return input_tensor, (orig_w, orig_h)

    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        input_tensor, orig_size = self.preprocess(image)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        
        # Post-process outputs (simplified for YOLOv8 format)
        # Assuming output shape: (1, 84, 8400) -> (1, 80 classes + 4 bbox + 1 obj_score, 8400)
        # This is a simplified post-processing logic; real implementation depends on specific ONNX export
        detections = []
        if len(outputs) > 0:
            pred = outputs[0].transpose(0, 2, 1) # (1, 8400, 84)
            # Filter by confidence (simplified)
            # In a real scenario, we'd use non-maximum suppression
            # Here we just take the max confidence per box
            scores = np.max(pred[:, :, 4:], axis=2) # Max class score
            # Simple threshold
            mask = scores > 0.25
            for i, is_detected in enumerate(mask[0]):
                if is_detected:
                    # Get best class
                    class_idx = np.argmax(pred[0, i, 4:])
                    score = pred[0, i, 4:][class_idx]
                    # Bbox: x_center, y_center, width, height -> x1, y1, x2, y2
                    x_center, y_center, w, h = pred[0, i, :4]
                    
                    # Scale back to original image
                    x1 = int((x_center - w/2) * orig_size[0] / self.input_size)
                    y1 = int((y_center - h/2) * orig_size[1] / self.input_size)
                    x2 = int((x_center + w/2) * orig_size[0] / self.input_size)
                    y2 = int((y_center + h/2) * orig_size[1] / self.input_size)
                    
                    # Clamp
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(orig_size[0], x2), min(orig_size[1], y2)
                    
                    detections.append({
                        "class": self.class_names[class_idx],
                        "bbox": [x1, y1, x2, y2],
                        "centroid": [(x1+x2)/2, (y1+y2)/2],
                        "confidence": float(score),
                        "color_hist": self._compute_color_hist(image, x1, y1, x2, y2)
                    })
        return detections

    def _compute_color_hist(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> List[float]:
        # Compute simple color histogram for the ROI
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            return [0.0] * 75 # 25 bins * 3 channels
        # Flatten and compute histogram
        hist = []
        for c in range(3):
            channel = roi[:,:,c]
            h, _ = np.histogram(channel, bins=25, range=(0, 256))
            hist.extend(h.astype(float) / h.sum() if h.sum() > 0 else [0.0]*25)
        return hist

class SymbolicTransformer:
    def __init__(self, model_path: str):
        self.yolo = YOLOv8ONNX(model_path)
        self.output_dir = get_path("processed", "symbolic_guava")
        os.makedirs(self.output_dir, exist_ok=True)

    def process_frame(self, frame: np.ndarray, frame_id: int, trajectory_id: str) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        
        # Check for empty frame (all black or very low variance)
        # This is a heuristic for "empty" scenes
        if frame.size == 0:
            # Explicitly handle empty frame case
            result = self._create_empty_symbolic_observation(frame_id, trajectory_id)
            self._log_perception_event(frame_id, trajectory_id, [], result)
            return result

        mean_intensity = np.mean(frame)
        if mean_intensity < 10: # Threshold for very dark/empty frame
            result = self._create_empty_symbolic_observation(frame_id, trajectory_id)
            self._log_perception_event(frame_id, trajectory_id, [], result)
            return result

        # Run detection
        detections = self.yolo.detect(frame)
        
        latency = time.time() - start_time
        log_latency(latency)

        # Create symbolic observation
        if len(detections) == 0:
            # Even if no objects detected, it's not necessarily an "empty scene" error
            # unless the frame itself was empty. We record the empty object list.
            result = SymbolicObservation(
                frame_id=frame_id,
                trajectory_id=trajectory_id,
                timestamp=datetime.now().isoformat(),
                detected_objects=[],
                scene_empty=False, # Detections failed, but scene might not be empty
                processing_time_ms=latency * 1000
            )
        else:
            result = SymbolicObservation(
                frame_id=frame_id,
                trajectory_id=trajectory_id,
                timestamp=datetime.now().isoformat(),
                detected_objects=detections,
                scene_empty=False,
                processing_time_ms=latency * 1000
            )

        self._log_perception_event(frame_id, trajectory_id, detections, result)
        return result

    def _create_empty_symbolic_observation(self, frame_id: int, trajectory_id: str) -> SymbolicObservation:
        """
        Handles the specific case of an empty frame (e.g., all black, no content).
        Returns a SymbolicObservation with scene_empty=True and empty object list.
        """
        return SymbolicObservation(
            frame_id=frame_id,
            trajectory_id=trajectory_id,
            timestamp=datetime.now().isoformat(),
            detected_objects=[],
            scene_empty=True,
            processing_time_ms=0.0
        )

    def _log_perception_event(self, frame_id: int, trajectory_id: str, detections: List[Dict], result: SymbolicObservation):
        # Prepare data for logger
        detected_objects = [
            {
                "class": d["class"],
                "bbox": d["bbox"],
                "centroid": d["centroid"],
                "color_hist": d["color_hist"]
            }
            for d in detections
        ]
        confidence_scores = [d["confidence"] for d in detections]
        
        # We need ground truth to determine object_missing_if_visible
        # For this implementation, we assume ground truth is loaded or available
        # In a real pipeline, this would be passed in or loaded from a file
        object_missing = False 
        # TODO: Integrate with ground truth loading for accurate object_missing_if_visible
        
        log_perception_ground_truth(
            timestamp=float(datetime.now().timestamp()),
            detected_objects=detected_objects,
            confidence_scores=confidence_scores,
            object_missing_if_visible=object_missing
        )

    def transform_trajectory(self, trajectory_path: str):
        trajectory_id = Path(trajectory_path).stem
        cap = cv2.VideoCapture(trajectory_path)
        
        if not cap.isOpened():
            raise SymbolicTransformationError(f"Could not open video: {trajectory_path}")
        
        frame_id = 0
        trajectory_data = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            obs = self.process_frame(frame, frame_id, trajectory_id)
            if obs:
                trajectory_data.append(obs.model_dump())
            frame_id += 1
        
        cap.release()
        
        # Save trajectory
        output_path = os.path.join(self.output_dir, f"{trajectory_id}.json")
        with open(output_path, 'w') as f:
            json.dump(trajectory_data, f, indent=2)
        
        return trajectory_data

def find_trajectories(data_dir: str) -> List[str]:
    # Search for video files
    patterns = ["*.mp4", "*.avi", "*.mov"]
    trajectories = []
    for pattern in patterns:
        trajectories.extend(glob.glob(os.path.join(data_dir, pattern)))
    return trajectories

def main():
    # Configuration
    model_path = get_path("artifacts", "yolov8n.onnx") # Default path, adjust as needed
    raw_data_dir = get_path("raw", "guava")
    
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}. Skipping transformation.")
        return

    transformer = SymbolicTransformer(model_path)
    trajectories = find_trajectories(raw_data_dir)
    
    print(f"Found {len(trajectories)} trajectories.")
    
    for traj_path in trajectories:
        print(f"Processing {traj_path}...")
        try:
            transformer.transform_trajectory(traj_path)
        except Exception as e:
            print(f"Error processing {traj_path}: {e}")

if __name__ == "__main__":
    main()