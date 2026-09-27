import json
import os
import sys
import time
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Local imports from existing API surface
from utils.config import get_path, get_hyperparameter
from utils.logger import compare_with_gt, log_perception_ground_truth, log_latency
from utils.errors import DatasetUnavailableError, PerceptionInferenceError
from data.models import SymbolicObservation, Trajectory, PerceptionLog
from data.models import serialize_trajectory, serialize_perception_log

# YOLO imports (defined in this file or imported from download_yolo if available)
# Assuming YOLOv8ONNX class is defined locally or imported as per T015a/b context
# We define it here to ensure the file is self-contained for execution if the module isn't fully loaded elsewhere yet,
# but strictly following the API surface, we assume the class exists or is defined in a way compatible with T015b.
# Since T015b asked for implementation in transform_symbolic.py, we ensure the logic is here.

try:
    import onnxruntime as ort
except ImportError:
    raise ImportError("onnxruntime is required. Install via requirements.txt")

class YOLOv8ONNX:
    """Wrapper for YOLOv8 ONNX model inference."""
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YOLO model not found at {model_path}")
        
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        
        # Class labels for Guava dataset (assuming standard COCO or specific Guava classes)
        # T015a implies a specific model, we use a standard mapping or load from config if needed.
        # For this implementation, we assume a standard 80-class COCO mapping or similar.
        # In a real scenario, this might be loaded from a config or a specific file.
        self.labels = [
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

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Resize and normalize frame for ONNX input."""
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if len(frame.shape) == 3 and frame.shape[2] == 3 else frame
        img = cv2.resize(img, (640, 640)) # Standard YOLOv8 input size
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1)) # CHW
        img = np.expand_dims(img, axis=0)
        return img

    def postprocess(self, output: np.ndarray, conf_thres: float = 0.5) -> List[Dict[str, Any]]:
        """Parse ONNX output into detections."""
        # Output shape depends on model, typically [1, 84, 8400] for YOLOv8n
        # 84 = 4 (bbox) + 80 (classes)
        if output.shape[1] == 84:
            output = output[0].T # [8400, 84]
            boxes = output[:, :4]
            scores = output[:, 4:]
            classes = np.argmax(scores, axis=1)
            confidences = np.max(scores, axis=1)
            
            detections = []
            for i, conf in enumerate(confidences):
                if conf > conf_thres:
                    x1, y1, w, h = boxes[i]
                    # Convert from center-x, center-y, w, h to x1, y1, x2, y2
                    x_center, y_center, width, height = boxes[i]
                    x1 = x_center - width / 2
                    y1 = y_center - height / 2
                    x2 = x1 + width
                    y2 = y1 + height
                    
                    detections.append({
                        'class_id': int(classes[i]),
                        'class_name': self.labels[classes[i]] if classes[i] < len(self.labels) else 'unknown',
                        'confidence': float(conf),
                        'bbox': [float(x1), float(y1), float(x2), float(y2)]
                    })
            return detections
        else:
            # Fallback for different output formats
            raise ValueError(f"Unexpected output shape: {output.shape}")

# Global instance to avoid reloading model on every call if used in a loop
_yolo_instance: Optional[YOLOv8ONNX] = None

def get_yolo_instance(model_path: str) -> YOLOv8ONNX:
    global _yolo_instance
    if _yolo_instance is None:
        _yolo_instance = YOLOv8ONNX(model_path)
    return _yolo_instance

def run_yolo_inference(frame: np.ndarray, model_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run YOLO inference on a single frame.
    T015b Implementation: Load model, run inference, return class, bbox, centroid, color histogram.
    """
    if model_path is None:
        model_path = get_path("yolo_model")
    
    try:
        yolo = get_yolo_instance(model_path)
        input_data = yolo.preprocess(frame)
        outputs = yolo.session.run(None, {yolo.input_name: input_data})
        detections = yolo.postprocess(outputs[0])
        
        # Enhance detections with centroid and color histogram if needed for SymbolicObservation
        for det in detections:
            # Calculate centroid
            bbox = det['bbox']
            det['centroid'] = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
            
            # Simple color histogram (mean color in bbox)
            # Assuming frame is BGR or RGB numpy array
            x1, y1, x2, y2 = [int(v) for v in bbox]
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                mean_color = np.mean(roi, axis=(0, 1)).tolist()
                det['color_histogram'] = mean_color
            else:
                det['color_histogram'] = [0, 0, 0]
                
        return detections
    except Exception as e:
        raise PerceptionInferenceError(f"YOLO inference failed: {str(e)}")

def find_trajectories(raw_data_dir: str) -> List[Path]:
    """Find all trajectory files (videos or image sequences) in the raw data directory."""
    trajectory_files = []
    # Support common video extensions and image sequence directories
    for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
        trajectory_files.extend(glob.glob(os.path.join(raw_data_dir, '**', ext), recursive=True))
    
    # Check for directories that might contain image sequences
    for item in os.listdir(raw_data_dir):
        item_path = os.path.join(raw_data_dir, item)
        if os.path.isdir(item_path):
            # Check if it contains images
            images = glob.glob(os.path.join(item_path, '*.jpg')) + glob.glob(os.path.join(item_path, '*.png'))
            if images:
                trajectory_files.append(Path(item_path))
                
    return [Path(p) for p in trajectory_files]

class SymbolicTransformer:
    """
    Main class to transform raw Guava trajectories into SymbolicObservations.
    Integrates T016a (GT Comparison) and T016b (Log Generation).
    """
    def __init__(self, raw_data_dir: str, output_dir: str, yolo_model_path: str):
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        self.yolo_model_path = yolo_model_path
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load Ground Truth if available
        gt_path = get_path("ground_truth_annotations")
        self.gt_data = None
        if os.path.exists(gt_path):
            try:
                with open(gt_path, 'r') as f:
                    self.gt_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load ground truth: {e}")
        else:
            print("Warning: Ground truth annotations not found. GT comparison will be skipped.")

    def _load_gt_for_trajectory(self, trajectory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve ground truth data for a specific trajectory."""
        if not self.gt_data:
            return None
        # Assuming gt_data structure: {"annotations": { "trajectory_id": [...] }}
        annotations = self.gt_data.get("annotations", {})
        return annotations.get(trajectory_id)

    def _process_frame(self, frame: np.ndarray, timestamp: float, trajectory_id: str) -> Dict[str, Any]:
        """Process a single frame: inference, GT comparison, logging."""
        start_time = time.time()
        
        # 1. Run YOLO Inference
        detections = run_yolo_inference(frame, self.yolo_model_path)
        
        # 2. Compare with Ground Truth (T016a)
        gt_info = self._load_gt_for_trajectory(trajectory_id)
        gt_objects = gt_info.get("bboxes", []) if gt_info else []
        
        comparison_result = compare_with_gt(
            detected_objects=detections,
            ground_truth_objects=gt_objects,
            iou_threshold=0.5
        )
        
        # 3. Log Perception and GT (T016b)
        log_entry = log_perception_ground_truth(
            timestamp=timestamp,
            detected_objects=detections,
            comparison_result=comparison_result
        )
        
        # 4. Log Latency
        latency = time.time() - start_time
        log_latency(timestamp, latency, "perception_inference")
        
        return log_entry

    def transform_trajectory(self, trajectory_path: Path):
        """Transform a single trajectory file into symbolic JSON."""
        trajectory_id = trajectory_path.stem
        print(f"Processing trajectory: {trajectory_id}")
        
        symbolic_observations = []
        
        # Logic to read frames depends on file type (video vs directory)
        # For this implementation, we assume a generic frame iterator or video reader
        # In a real scenario, we'd use cv2.VideoCapture for videos or iterate images for directories
        
        try:
            if trajectory_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                import cv2
                cap = cv2.VideoCapture(str(trajectory_path))
                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    timestamp = frame_count / cap.get(cv2.CAP_PROP_FPS)
                    log_entry = self._process_frame(frame, timestamp, trajectory_id)
                    symbolic_observations.append(log_entry)
                    frame_count += 1
                cap.release()
            elif trajectory_path.is_dir():
                # Handle image sequence directory
                images = sorted([p for p in trajectory_path.iterdir() if p.suffix.lower() in ['.jpg', '.png', '.jpeg']])
                for i, img_path in enumerate(images):
                    import cv2
                    frame = cv2.imread(str(img_path))
                    if frame is None:
                        continue
                    timestamp = i # Assuming 1fps or index-based time
                    log_entry = self._process_frame(frame, timestamp, trajectory_id)
                    symbolic_observations.append(log_entry)
            else:
                print(f"Skipping unsupported trajectory format: {trajectory_path}")
                return
        except Exception as e:
            print(f"Error processing trajectory {trajectory_id}: {e}")
            return

        # Save output
        output_file = self.output_dir / f"{trajectory_id}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "trajectory_id": trajectory_id,
                "observations": symbolic_observations,
                "metadata": {
                    "source": str(trajectory_path),
                    "processed_at": datetime.now().isoformat(),
                    "model_used": self.yolo_model_path
                }
            }, f, indent=2)
        print(f"Saved symbolic observations to {output_file}")

    def run(self):
        """Run transformation on all found trajectories."""
        trajectories = find_trajectories(str(self.raw_data_dir))
        print(f"Found {len(trajectories)} trajectories.")
        
        for traj in trajectories:
            self.transform_trajectory(traj)

def main():
    """Entry point for the transformation pipeline."""
    # Initialize paths from config
    raw_dir = get_path("raw_data")
    out_dir = get_path("processed_data")
    yolo_path = get_path("yolo_model")
    
    # Check constraints
    from utils.env_config import check_cpu_constraints
    check_cpu_constraints()
    
    if not os.path.exists(yolo_path):
        raise FileNotFoundError(f"YOLO model not found at {yolo_path}. Run T015a first.")
    
    transformer = SymbolicTransformer(raw_dir, out_dir, yolo_path)
    transformer.run()

if __name__ == "__main__":
    main()