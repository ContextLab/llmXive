import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import cv2
import onnxruntime as ort
from pydantic import ValidationError

# Local imports matching API surface
from data.models import SymbolicObservation, PerceptionLog, serialize_perception_log
from utils.exceptions import PerceptionInferenceError, SymbolicTransformationError
from utils.config import ensure_directories
from utils.logger import log_perception_ground_truth, log_latency
from utils.environment_config import configure_torch_for_cpu

# Ensure CPU optimization if running on CPU
configure_torch_for_cpu()

class YOLOv8ONNX:
    """Wrapper for YOLOv8 ONNX model inference."""

    def __init__(self, model_path: str, conf_thres: float = 0.25, iou_thres: float = 0.45):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YOLO model not found at {model_path}")
        
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.input_shape = self.session.get_inputs()[0].shape[2:4] # (H, W)

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for ONNX input."""
        h, w = frame.shape[:2]
        input_h, input_w = self.input_shape
        
        # Resize and pad to maintain aspect ratio (letterbox)
        scale = min(input_w / w, input_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h))
        
        # Pad
        pad_w = (input_w - new_w) // 2
        pad_h = (input_h - new_h) // 2
        padded = cv2.copyMakeBorder(resized, pad_h, input_h - new_h - pad_h, 
                                    pad_w, input_w - new_w - pad_w, 
                                    cv2.BORDER_CONSTANT, value=(114, 114, 114))
        
        # Normalize and convert to float32
        img = padded.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1) # HWC -> CHW
        img = np.expand_dims(img, 0) # Add batch dim
        return img

    def postprocess(self, output: np.ndarray, original_shape: tuple) -> List[Dict[str, Any]]:
        """Postprocess YOLO output to get detections."""
        h, w = original_shape
        input_h, input_w = self.input_shape
        
        # Output shape: (1, 84, 8400) for YOLOv8n
        # 84 = 4 (bbox) + 80 (classes)
        detections = []
        
        # Transpose to (8400, 84) for easier processing
        preds = output[0].transpose(1, 0)
        
        # Filter by confidence
        scores = np.max(preds[:, 4:], axis=1)
        valid_idx = np.where(scores >= self.conf_thres)[0]
        
        if len(valid_idx) == 0:
            return []
        
        boxes = preds[valid_idx, :4]
        class_ids = np.argmax(preds[valid_idx, 4:], axis=1)
        confs = scores[valid_idx]
        
        # Non-maximum suppression
        nms_idx = cv2.dnn.NMSBoxes(
            boxes.tolist(), 
            confs.tolist(), 
            score_threshold=self.conf_thres, 
            nms_threshold=self.iou_thres
        )
        
        if len(nms_idx) == 0:
            return []
        
        for i in nms_idx:
            idx = valid_idx[i]
            box = boxes[i]
            cls = class_ids[i]
            conf = confs[i]
            
            # Unscale coordinates
            scale = min(input_w / w, input_h / h)
            pad_w = (input_w - int(w * scale)) // 2
            pad_h = (input_h - int(h * scale)) // 2
            
            x1 = (box[0] - box[2]/2 - pad_w) / scale
            y1 = (box[1] - box[3]/2 - pad_h) / scale
            x2 = (box[0] + box[2]/2 - pad_w) / scale
            y2 = (box[1] + box[3]/2 - pad_h) / scale
            
            # Clamp to image bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            detections.append({
                "class_id": int(cls),
                "class_name": self._get_class_name(cls),
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": float(conf),
                "centroid": [(x1 + x2) / 2, (y1 + y2) / 2]
            })
        
        return detections

    def _get_class_name(self, class_id: int) -> str:
        """Map class ID to name (simplified COCO classes)."""
        # Simplified mapping for demo; in real impl, use full COCO map
        coco_names = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
            5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
            10: 'fire hydrant', 13: 'stop sign', 14: 'parking meter', 15: 'bench',
            16: 'bird', 17: 'cat', 18: 'dog', 19: 'horse', 20: 'sheep',
            21: 'cow', 22: 'elephant', 23: 'bear', 24: 'zebra', 25: 'giraffe'
        }
        return coco_names.get(class_id, f"object_{class_id}")

class SymbolicTransformer:
    """Transforms raw video frames into symbolic observations."""

    def __init__(self, model_path: str, output_dir: str):
        self.detector = YOLOv8ONNX(model_path)
        self.output_dir = Path(output_dir)
        ensure_directories([self.output_dir])
        self.perception_log_path = self.output_dir.parent / "artifacts" / "perception_log.json"
        ensure_directories([self.perception_log_path.parent])

    def process_frame(self, frame: np.ndarray, frame_id: int, trajectory_id: str) -> SymbolicObservation:
        """Process a single frame and return symbolic observation."""
        start_time = time.time()
        
        h, w = frame.shape[:2]
        detections = self.detector.preprocess(frame)
        if not detections:
            detections = []
        else:
            raw_output = self.detector.session.run(None, {self.detector.input_name: detections})
            detections = self.detector.postprocess(raw_output[0], (h, w))
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Handle empty frames logic (T017)
        is_empty = len(detections) == 0
        scene_empty_flag = "scene_empty" if is_empty else None
        
        # Construct objects list
        objects_list = []
        if not is_empty:
            for det in detections:
                # Calculate color histogram (simplified)
                x1, y1, x2, y2 = map(int, det['bbox'])
                roi = frame[y1:y2, x1:x2]
                if roi.size > 0:
                    # Simple mean color as histogram proxy
                    mean_color = np.mean(roi, axis=(0, 1)).tolist()
                    objects_list.append({
                        "class_id": det['class_id'],
                        "class_name": det['class_name'],
                        "bbox": det['bbox'],
                        "centroid": det['centroid'],
                        "confidence": det['confidence'],
                        "color_histogram": mean_color
                    })
        
        # Create SymbolicObservation
        obs = SymbolicObservation(
            frame_id=frame_id,
            timestamp=datetime.now().isoformat(),
            image_size={"width": w, "height": h},
            objects=objects_list,
            scene_empty=scene_empty_flag,
            perception_latency_ms=latency_ms
        )
        
        # Log to PerceptionLog (T016/T018 integration)
        log_entry = {
            "trajectory_id": trajectory_id,
            "frame_id": frame_id,
            "timestamp": obs.timestamp,
            "object_count": len(objects_list),
            "scene_empty": is_empty,
            "latency_ms": latency_ms,
            "object_missing_if_visible": False # Placeholder for T016 logic
        }
        log_perception_ground_truth(log_entry, self.perception_log_path)
        log_latency(latency_ms, self.perception_log_path)
        
        return obs

    def transform_trajectory(self, video_path: str, trajectory_id: str) -> List[Dict[str, Any]]:
        """Process a full video trajectory."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise PerceptionInferenceError(f"Failed to open video: {video_path}")
        
        frame_count = 0
        observations = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                obs = self.process_frame(frame, frame_count, trajectory_id)
                observations.append(obs.model_dump())
                frame_count += 1
            except Exception as e:
                raise SymbolicTransformationError(f"Failed to process frame {frame_count}: {str(e)}")
        
        cap.release()
        
        # Save trajectory output
        output_path = self.output_dir / f"{trajectory_id}.json"
        with open(output_path, 'w') as f:
            json.dump(observations, f, indent=2)
        
        return observations

def main():
    """Main entry point for symbolic transformation."""
    # Example usage - in real pipeline, args would be parsed
    model_path = "data/models/yolov8n.onnx" # Placeholder path
    raw_data_dir = "data/raw/guava"
    processed_dir = "data/processed/symbolic_guava"
    
    if not os.path.exists(model_path):
        print(f"Warning: Model not found at {model_path}. Skipping execution.")
        return

    transformer = SymbolicTransformer(model_path, processed_dir)
    
    # Process sample trajectories if they exist
    if os.path.exists(raw_data_dir):
        for video_file in Path(raw_data_dir).glob("*.mp4"):
            traj_id = video_file.stem
            try:
                transformer.transform_trajectory(str(video_file), traj_id)
                print(f"Processed: {traj_id}")
            except Exception as e:
                print(f"Error processing {traj_id}: {e}")

if __name__ == "__main__":
    main()