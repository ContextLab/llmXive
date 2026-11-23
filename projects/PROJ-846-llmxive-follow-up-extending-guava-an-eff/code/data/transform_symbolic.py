"""
Symbolic Transformation Pipeline for Guava Dataset.

This module ingests raw video frames from the Guava dataset, runs YOLO-tiny
inference to extract symbolic observations (bounding boxes, class labels,
centroids, color histograms), and emits the results as JSON files.

Dependencies:
- code/data/models.py (SymbolicObservation, PerceptionLog, Trajectory, TaskOutcome)
- code/utils/config.py (get_path, get_hyperparameter)
- code/utils/errors.py (DatasetUnavailableError)
- code/utils/env_config.py (check_cpu_constraints)
- code/data/download_yolo.py (for model path verification)
"""

import json
import os
import sys
import time
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import onnxruntime as ort
from PIL import Image

# Project relative imports
from data.models import (
    SymbolicObservation,
    Trajectory,
    TaskOutcome,
    PerceptionLog,
    serialize_trajectory,
    serialize_outcome,
    FailureType,
    PerceptionQuality
)
from utils.config import get_path, get_hyperparameter, ensure_directories
from utils.errors import DatasetUnavailableError
from utils.env_config import check_cpu_constraints

# Constants
DEFAULT_IMAGE_SIZE = (640, 640)
LATENCY_THRESHOLD_MS = 150.0
CONFIDENCE_THRESHOLD = 0.25


class YOLOv8ONNX:
    """Wrapper for YOLOv8n ONNX model inference."""

    def __init__(self, model_path: str, img_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE):
        self.model_path = model_path
        self.img_size = img_size
        self.session = None
        self.input_name = None
        self.output_name = None
        self._load_model()

    def _load_model(self):
        """Load the ONNX model and verify it exists."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"YOLO model not found at {self.model_path}. "
                                    "Run T015a to download the model.")

        # Enforce CPU-only execution as per project constraints
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        sess_options = ort.InferenceSession(self.model_path, sess_options=opts, providers=['CPUExecutionProvider'])

        self.session = sess_options
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def infer(self, image: np.ndarray) -> np.ndarray:
        """
        Run inference on a single image.
        Args:
            image: numpy array of shape (H, W, 3) in uint8.
        Returns:
            numpy array of detections.
        """
        if self.session is None:
            raise RuntimeError("Model not loaded.")

        # Preprocess: Resize, Normalize, CHW, Batch
        img_pil = Image.fromarray(image)
        img_resized = img_pil.resize(self.img_size, Image.LANCZOS)
        img_array = np.array(img_resized).astype(np.float32) / 255.0
        img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, axis=0)

        # Run inference
        start_time = time.perf_counter()
        outputs = self.session.run(None, {self.input_name: img_array})
        inference_time = (time.perf_counter() - start_time) * 1000.0

        return outputs[0], inference_time


def get_yolo_instance() -> YOLOv8ONNX:
    """Factory function to get a configured YOLO instance."""
    model_path = get_path("yolo_model_path")
    if not model_path:
        # Fallback to default if config is missing, though T015a should set it
        model_path = str(get_path("models_dir") / "yolo_tiny.onnx")
    return YOLOv8ONNX(model_path)


def run_yolo_inference(yolo_model: YOLOv8ONNX, frame_path: str) -> Tuple[List[Dict[str, Any]], float]:
    """
    Run YOLO inference on a single frame.
    Returns:
        Tuple of (list of detection dicts, inference_time_ms)
    """
    try:
        image = np.array(Image.open(frame_path).convert("RGB"))
    except Exception as e:
        raise RuntimeError(f"Failed to load image {frame_path}: {e}")

    detections_raw, inference_time = yolo_model.infer(image)

    # Post-processing: YOLOv8 output shape is usually (1, 84, 8400) -> (84, 8400)
    # 84 = 4 bbox + 80 classes
    # We need to transpose and filter
    if detections_raw.shape[1] == 84:
        detections_raw = detections_raw[0].T  # (8400, 84)

    detections = []
    num_classes = 80 # Assuming COCO classes for YOLOv8n

    for det in detections_raw:
        # det: [x_center, y_center, w, h, class_probs...]
        conf = float(np.max(det[4:]))
        if conf < CONFIDENCE_THRESHOLD:
            continue

        cls_id = int(np.argmax(det[4:]))
        x_c, y_c, w, h = det[:4]

        # Convert to x_min, y_min, x_max, y_max
        x_min = max(0, int(x_c - w / 2))
        y_min = max(0, int(y_c - h / 2))
        x_max = int(x_c + w / 2)
        y_max = int(y_c + h / 2)

        # Centroid
        centroid_x = int((x_min + x_max) / 2)
        centroid_y = int((y_min + y_max) / 2)

        # Color histogram (simple mean color in bbox)
        roi = image[y_min:y_max, x_min:x_max]
        if roi.size > 0:
            mean_color = tuple(map(int, np.mean(roi, axis=(0, 1))))
        else:
            mean_color = (0, 0, 0)

        detections.append({
            "class_id": cls_id,
            "bbox": [x_min, y_min, x_max, y_max],
            "centroid": [centroid_x, centroid_y],
            "confidence": conf,
            "color_mean": mean_color,
            "inference_time_ms": inference_time
        })

    return detections, inference_time


def find_trajectories(raw_data_dir: Path) -> List[Path]:
    """
    Scan the raw data directory for trajectory directories.
    Expected structure: raw_data_dir / {trajectory_id} / frame_*.jpg
    """
    if not raw_data_dir.exists():
        raise DatasetUnavailableError(f"Raw data directory not found: {raw_data_dir}")

    trajectories = []
    # Assuming each subdirectory is a trajectory
    for item in raw_data_dir.iterdir():
        if item.is_dir():
            # Check if it contains images
            if list(item.glob("*.jpg")) or list(item.glob("*.png")):
                trajectories.append(item)
    return sorted(trajectories)


def process_frame(frame_path: Path, yolo_model: YOLOv8ONNX) -> SymbolicObservation:
    """
    Process a single frame and return a SymbolicObservation.
    """
    detections, latency = run_yolo_inference(yolo_model, str(frame_path))

    # Create objects list
    objects = [
        SymbolicObservation(
            class_id=d["class_id"],
            bbox=d["bbox"],
            centroid=d["centroid"],
            confidence=d["confidence"],
            color_mean=d["color_mean"]
        )
        for d in detections
    ]

    # Determine scene status
    is_empty = len(objects) == 0

    return SymbolicObservation(
        timestamp=datetime.now().isoformat(),
        frame_path=str(frame_path),
        objects=objects,
        is_empty=is_empty,
        latency_ms=latency,
        latency_exceeded=latency > LATENCY_THRESHOLD_MS
    )


class SymbolicTransformer:
    """Main orchestrator for the symbolic transformation pipeline."""

    def __init__(self):
        self.yolo_model = get_yolo_instance()
        self.raw_data_dir = get_path("raw_data_dir")
        self.output_dir = get_path("processed_symbolic_dir")
        ensure_directories([self.output_dir])
        self.processed_count = 0
        self.latency_failures = 0

    def transform(self):
        """
        Run the full transformation pipeline.
        1. Find trajectories.
        2. Process each frame in each trajectory.
        3. Aggregate into Trajectory object.
        4. Save to JSON.
        5. Save TaskOutcome.
        """
        trajectories = find_trajectories(self.raw_data_dir)
        if not trajectories:
            print(f"Warning: No trajectories found in {self.raw_data_dir}")
            return

        print(f"Found {len(trajectories)} trajectories. Starting transformation...")

        for traj_path in trajectories:
            traj_id = traj_path.name
            print(f"Processing trajectory: {traj_id}")

            frame_paths = sorted(list(traj_path.glob("*.jpg")) + list(traj_path.glob("*.png")))
            if not frame_paths:
                print(f"  No frames found for {traj_id}")
                continue

            symbolic_observations = []
            total_frame_latency = 0.0
            max_frame_latency = 0.0
            has_latency_failure = False

            for frame_path in frame_paths:
                try:
                    obs = process_frame(frame_path, self.yolo_model)
                    symbolic_observations.append(obs)

                    total_frame_latency += obs.latency_ms
                    if obs.latency_ms > max_frame_latency:
                        max_frame_latency = obs.latency_ms
                    if obs.latency_exceeded:
                        has_latency_failure = True
                        self.latency_failures += 1

                except Exception as e:
                    print(f"  Error processing {frame_path.name}: {e}")
                    # Continue to next frame, but log error
                    continue

            # Create Trajectory object
            trajectory = Trajectory(
                trajectory_id=traj_id,
                frame_count=len(symbolic_observations),
                observations=symbolic_observations,
                avg_latency_ms=total_frame_latency / len(symbolic_observations) if symbolic_observations else 0.0,
                max_latency_ms=max_frame_latency,
                has_latency_failure=has_latency_failure,
                processed_at=datetime.now().isoformat()
            )

            # Serialize and save
            output_file = self.output_dir / f"{traj_id}.json"
            with open(output_file, 'w') as f:
                json.dump(trajectory.model_dump(), f, indent=2)
            
            self.processed_count += 1
            print(f"  Saved: {output_file}")

        # Generate a summary TaskOutcome for the whole run
        total_time = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        outcome = TaskOutcome(
            run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            status="completed",
            total_trajectories=len(trajectories),
            processed_trajectories=self.processed_count,
            total_latency_failures=self.latency_failures,
            latency_threshold_ms=LATENCY_THRESHOLD_MS,
            execution_time_seconds=total_time,
            success_rate=(self.processed_count / len(trajectories)) if trajectories else 0.0
        )

        outcome_file = self.output_dir / "transformation_outcome.json"
        with open(outcome_file, 'w') as f:
            json.dump(outcome.model_dump(), f, indent=2)
        
        print(f"Transformation complete. Outcome saved to {outcome_file}")

    def run(self):
        """Entry point."""
        self.start_time = time.time()
        check_cpu_constraints() # Enforce CPU constraint
        self.transform()


def main():
    """Main entry point for the script."""
    transformer = SymbolicTransformer()
    transformer.run()


if __name__ == "__main__":
    main()