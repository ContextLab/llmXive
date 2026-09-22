import json
import os
import sys
import time
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
import onnxruntime as ort

# Import project utilities and exceptions
from utils.config import get_path, get_hyperparameter, set_global_seed
from utils.exceptions import SymbolicTransformationError, DatasetUnavailableError
from data.models import SymbolicObservation, serialize_trajectory

class YOLOv8ONNX:
    """
    Wrapper for YOLOv8 ONNX model inference.
    Handles loading, preprocessing, and postprocessing of object detection.
    """
    def __init__(self, model_path: str, conf_thresh: float = 0.25, iou_thresh: float = 0.45):
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.output_names = [o.name for o in self.session.get_outputs()]
        
        # Load class names if available in the model metadata or use defaults
        # For Guava, we assume standard COCO-like classes or specific domain objects
        self.classes = self._load_class_names()

    def _load_class_names(self) -> List[str]:
        # Default COCO classes for YOLOv8
        return [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
            'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
            'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
            'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
            'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Resize and normalize image for ONNX model."""
        input_h, input_w = self.input_shape[2], self.input_shape[3]
        original_h, original_w = image.shape[:2]
        
        # Resize
        resized = cv2.resize(image, (input_w, input_h), interpolation=cv2.INTER_LINEAR)
        
        # Normalize to [0, 1] and convert to float32
        normalized = resized.astype(np.float32) / 255.0
        
        # Transpose to (1, 3, H, W) format expected by ONNX
        if normalized.ndim == 3:
            normalized = np.transpose(normalized, (2, 0, 1))
        normalized = np.expand_dims(normalized, axis=0)
        
        return normalized

    def postprocess(self, outputs: List[np.ndarray], original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Process raw model outputs into bounding boxes and classes."""
        # YOLOv8 outputs are typically [1, 84, 8400] where 84 = 4 bbox + 80 classes
        # We need to transpose and filter
        output = outputs[0]
        
        # Transpose to [1, 8400, 84]
        output = np.transpose(output, (0, 2, 1))
        
        # Extract boxes, scores, and classes
        boxes = output[:, :, :4]
        scores = output[:, :, 4:]
        
        # Non-maximum suppression and filtering
        detections = []
        batch_size = boxes.shape[0]
        
        for b in range(batch_size):
            box_batch = boxes[b]
            score_batch = scores[b]
            
            # Find max score and class index for each detection
            max_scores = np.max(score_batch, axis=1)
            class_indices = np.argmax(score_batch, axis=1)
            
            # Filter by confidence threshold
            valid_indices = np.where(max_scores >= self.conf_thresh)[0]
            
            for idx in valid_indices:
                x1, y1, x2, y2 = box_batch[idx]
                # Convert from (x_center, y_center, w, h) to (x1, y1, x2, y2)
                x_center, y_center, w, h = x1, y1, x2, y2
                x1 = x_center - w / 2
                y1 = y_center - h / 2
                x2 = x_center + w / 2
                y2 = y_center + h / 2
                
                # Clamp to image boundaries
                orig_h, orig_w = original_shape
                x1 = max(0, min(x1, orig_w))
                y1 = max(0, min(y1, orig_h))
                x2 = max(0, min(x2, orig_w))
                y2 = max(0, min(y2, orig_h))
                
                if x2 <= x1 or y2 <= y1:
                    continue
                    
                detections.append({
                    'class': self.classes[class_indices[idx]] if class_indices[idx] < len(self.classes) else 'unknown',
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': float(max_scores[idx]),
                    'centroid': [(x1 + x2) / 2, (y1 + y2) / 2]
                })
        
        # Apply NMS
        if len(detections) > 1:
            boxes_arr = np.array([d['bbox'] for d in detections], dtype=np.float32)
            scores_arr = np.array([d['confidence'] for d in detections])
            indices = cv2.dnn.NMSBoxes(
                [b.tolist() for b in boxes_arr], 
                scores_arr.tolist(), 
                self.conf_thresh, 
                self.iou_thresh
            )
            if len(indices) > 0:
                indices = indices.flatten()
                detections = [detections[i] for i in indices]
            else:
                detections = []
        
        return detections

    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Run detection on a single image."""
        preprocessed = self.preprocess(image)
        outputs = self.session.run(self.output_names, {self.input_name: preprocessed})
        return self.postprocess(outputs, image.shape[:2])

    def compute_color_histogram(self, image: np.ndarray, bbox: List[int]) -> List[float]:
        """Compute normalized color histogram for a detected object."""
        x1, y1, x2, y2 = bbox
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            return [0.0] * 256
        
        # Compute histogram for each channel
        hist = []
        for channel in range(3):
            channel_hist = np.histogram(roi[:, :, channel], bins=256, range=(0, 256))[0]
            normalized_hist = channel_hist / channel_hist.sum() if channel_hist.sum() > 0 else np.zeros(256)
            hist.extend(normalized_hist.tolist())
        
        return hist

class SymbolicTransformer:
    """
    Transforms raw video frames into symbolic observations.
    Handles empty frames and scene_empty flags.
    """
    def __init__(self, model_path: str, conf_thresh: float = 0.25, iou_thresh: float = 0.45):
        self.yolo = YOLOv8ONNX(model_path, conf_thresh, iou_thresh)
        self.config = {
            'conf_thresh': conf_thresh,
            'iou_thresh': iou_thresh
        }

    def process_frame(self, frame: np.ndarray, frame_id: int, trajectory_id: str) -> SymbolicObservation:
        """
        Process a single frame and return a SymbolicObservation.
        
        Handles empty frames by setting scene_empty flag and empty object list.
        """
        start_time = time.time()
        
        # Run detection
        detections = self.yolo.detect(frame)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Check if frame is empty (no detections)
        is_empty = len(detections) == 0
        
        # Prepare detected objects list
        detected_objects = []
        for det in detections:
            # Compute color histogram
            color_hist = self.yolo.compute_color_histogram(frame, det['bbox'])
            
            obj = {
                'class': det['class'],
                'bbox': det['bbox'],
                'centroid': det['centroid'],
                'color_hist': color_hist,
                'confidence': det['confidence']
            }
            detected_objects.append(obj)
        
        # Create SymbolicObservation
        obs = SymbolicObservation(
            trajectory_id=trajectory_id,
            frame_id=frame_id,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time * 1000,
            detected_objects=detected_objects,
            scene_empty=is_empty,
            frame_dimensions={'width': frame.shape[1], 'height': frame.shape[0]}
        )
        
        return obs

    def transform_trajectory(self, video_path: Path, trajectory_id: str) -> List[SymbolicObservation]:
        """
        Transform an entire video trajectory into symbolic observations.
        
        Returns a list of SymbolicObservation objects, one per frame.
        """
        if not video_path.exists():
            raise DatasetUnavailableError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise SymbolicTransformationError(f"Failed to open video: {video_path}")
        
        observations = []
        frame_id = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                obs = self.process_frame(frame, frame_id, trajectory_id)
                observations.append(obs)
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing frame {frame_id} in {trajectory_id}: {e}")
            
            frame_id += 1
        
        cap.release()
        return observations

def find_trajectories(data_dir: str) -> List[Tuple[Path, str]]:
    """
    Find all trajectory video files in the data directory.
    
    Returns a list of tuples (video_path, trajectory_id).
    """
    trajectories = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise DatasetUnavailableError(f"Data directory not found: {data_dir}")
    
    # Look for video files in subdirectories or directly
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    for ext in video_extensions:
        for video_file in data_path.rglob(f"*{ext}"):
            # Extract trajectory ID from filename or directory structure
            trajectory_id = video_file.stem
            # If in a subdirectory, use directory name as part of ID
            if video_file.parent != data_path:
                trajectory_id = f"{video_file.parent.name}_{trajectory_id}"
            
            trajectories.append((video_file, trajectory_id))
    
    return trajectories

def main():
    """Main entry point for the symbolic transformation pipeline."""
    # Load configuration
    set_global_seed(42)
    data_dir = get_path('raw_guava')
    output_dir = get_path('processed_symbolic')
    model_path = get_path('yolo_model')
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize transformer
    transformer = SymbolicTransformer(model_path)
    
    # Find all trajectories
    trajectories = find_trajectories(data_dir)
    print(f"Found {len(trajectories)} trajectories to process")
    
    total_frames = 0
    empty_frames = 0
    
    for video_path, trajectory_id in trajectories:
        print(f"Processing trajectory: {trajectory_id}")
        try:
            observations = transformer.transform_trajectory(video_path, trajectory_id)
            
            # Write observations to JSON file
            output_file = Path(output_dir) / f"{trajectory_id}.json"
            
            # Serialize observations
            serialized = []
            for obs in observations:
                serialized.append(obs.model_dump())
                total_frames += 1
                if obs.scene_empty:
                    empty_frames += 1
            
            with open(output_file, 'w') as f:
                json.dump(serialized, f, indent=2)
            
            print(f"  -> Wrote {len(observations)} frames to {output_file}")
            print(f"     Empty frames: {sum(1 for o in observations if o.scene_empty)}")
            
        except Exception as e:
            print(f"Error processing trajectory {trajectory_id}: {e}")
            # Continue with next trajectory
            continue
    
    print(f"Transformation complete. Processed {total_frames} frames, {empty_frames} empty.")
    print(f"Output directory: {output_dir}")

if __name__ == '__main__':
    main()