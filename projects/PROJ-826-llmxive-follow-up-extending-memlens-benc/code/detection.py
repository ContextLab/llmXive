import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Third-party imports (ensure ultralytics is in requirements.txt)
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from utils.logger import get_detection_logger, log_detection_status, log_fallback_event
from preprocessing import preprocess_image

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "metrics"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-826-llmxive-follow-up-extending-memlens-benc.yaml"
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "memlens"

# Ensure output directory exists
DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

def load_yolo_model(model_name: str = "yolov8n.pt") -> Optional[Any]:
    """
    Loads the YOLOv8-Tiny (nano) model.
    Returns None if the library is not installed.
    """
    if not YOLO_AVAILABLE:
        log_fallback_event("YOLO library not installed. Please install ultralytics.")
        return None
    
    try:
        model = YOLO(model_name)
        # Explicitly set to CPU to comply with project constraints
        model.to("cpu")
        return model
    except Exception as e:
        log_fallback_event(f"Failed to load YOLO model: {str(e)}")
        return None

def check_ground_truth_exists(sample: Dict[str, Any]) -> bool:
    """
    Checks if the sample contains ground-truth bounding box information.
    MemLens dataset structure usually puts GT in 'annotations' or similar.
    We look for 'bbox' or 'ground_truth_boxes' keys.
    """
    # Check common keys for bounding boxes in the sample
    possible_keys = ['bbox', 'ground_truth_boxes', 'bboxes', 'annotations']
    for key in possible_keys:
        if key in sample:
            val = sample[key]
            if isinstance(val, list) and len(val) > 0:
                return True
            # Sometimes it's a nested structure
            if isinstance(val, dict) and val:
                return True
    return False

def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculates Intersection over Union (IoU) between two boxes.
    Boxes are expected in [x_min, y_min, x_max, y_max] format.
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union_area = box1_area + box2_area - inter_area
    if union_area == 0:
        return 0.0
    return inter_area / union_area

def run_object_detection(
    model: Any,
    sample: Dict[str, Any],
    image_path: Path,
    iou_threshold: float = 0.5
) -> Tuple[str, List[Dict], Optional[float]]:
    """
    Runs YOLOv8 detection on an image.
    Returns:
      - status: 'success', 'zero_detection', or 'fallback'
      - detected_boxes: List of dicts with 'bbox', 'confidence', 'class'
      - recall: Float if GT exists, else None
    """
    if not YOLO_AVAILABLE:
        return 'fallback', [], None

    try:
        # Preprocess image to ensure compatibility
        # preprocess_image handles loading and basic normalization if needed
        # YOLO expects a path or numpy array
        result = model(image_path)
        
        # Extract detections
        # result[0].boxes contains boxes, conf, cls
        boxes = result[0].boxes
        detected_boxes = []
        
        if boxes is not None and len(boxes) > 0:
            for i in range(len(boxes)):
                # xyxy format from YOLO
                xyxy = boxes.xyxy[i].cpu().numpy().tolist()
                conf = float(boxes.conf[i].cpu().numpy())
                cls = int(boxes.cls[i].cpu().numpy())
                detected_boxes.append({
                    "bbox": xyxy,
                    "confidence": conf,
                    "class_id": cls
                })
        
        if len(detected_boxes) == 0:
            return 'zero_detection', [], None

        # Calculate Recall if GT exists
        recall = None
        if check_ground_truth_exists(sample):
            # Extract GT boxes from sample
            # Assuming GT is a list of [x_min, y_min, x_max, y_max]
            gt_boxes = sample.get('bbox', sample.get('ground_truth_boxes', []))
            
            # Handle different GT formats if necessary
            # If GT is a list of lists
            if gt_boxes and isinstance(gt_boxes[0], (list, tuple)):
                gt_list = [list(b) for b in gt_boxes]
            else:
                # Fallback or other format handling if needed
                gt_list = []

            tp_count = 0
            fn_count = len(gt_list)
            matched_gt_indices = set()

            for det in detected_boxes:
                det_box = det['bbox']
                best_iou = 0
                best_gt_idx = -1

                for idx, gt_box in enumerate(gt_list):
                    if idx in matched_gt_indices:
                        continue
                    iou = calculate_iou(det_box, gt_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = idx

                if best_iou >= iou_threshold and best_gt_idx != -1:
                    tp_count += 1
                    matched_gt_indices.add(best_gt_idx)
            
            fn_count = len(gt_list) - len(matched_gt_indices)
            denominator = tp_count + fn_count
            if denominator > 0:
                recall = tp_count / denominator
            else:
                recall = 0.0

        return 'success', detected_boxes, recall

    except Exception as e:
        log_fallback_event(f"YOLO detection failed for {image_path}: {str(e)}")
        return 'fallback', [], None

def process_dataset_for_detection() -> Dict[str, Any]:
    """
    Iterates through the processed MemLens dataset, runs detection,
    and aggregates metrics.
    """
    if not YOLO_AVAILABLE:
        log_fallback_event("Cannot process dataset: YOLO library missing.")
        return {"error": "YOLO library missing"}

    model = load_yolo_model("yolov8n.pt")
    if model is None:
        return {"error": "Failed to load YOLO model"}

    logger = get_detection_logger()
    logger.info("Starting YOLOv8 detection pipeline on MemLens dataset.")

    # Locate the JSONL or processed data file
    # Assuming T006/T008 created a processed JSONL file in data/processed
    # We look for the most recent or standard file
    processed_dir = PROJECT_ROOT / "data" / "processed"
    data_file = None
    
    # Heuristic: look for a file named 'memlens_processed.jsonl' or similar
    candidates = list(processed_dir.glob("*.jsonl"))
    if not candidates:
        # Fallback to raw if processed doesn't exist yet (should be T004 output)
        raw_candidates = list((PROJECT_ROOT / "data" / "raw" / "memlens").glob("*.jsonl"))
        if raw_candidates:
            data_file = raw_candidates[0]
        else:
            raise FileNotFoundError("No dataset file found in data/raw or data/processed")
    else:
        data_file = candidates[0]

    if not data_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_file}")

    total_samples = 0
    success_count = 0
    zero_detection_count = 0
    fallback_count = 0
    recall_values = []
    gt_present_count = 0
    gt_missing_count = 0

    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            sample = json.loads(line)
            total_samples += 1
            
            # Determine image path
            # MemLens samples usually have an 'image' or 'image_path' field
            img_path_str = sample.get('image_path') or sample.get('image')
            
            if not img_path_str:
                # Try to construct from ID if path is missing
                sample_id = sample.get('id', 'unknown')
                # Assuming raw data structure: data/raw/memlens/images/{id}.jpg
                potential_path = RAW_DATA_PATH / "images" / f"{sample_id}.jpg"
                if potential_path.exists():
                    img_path_str = str(potential_path)
                else:
                    log_fallback_event(f"Image path missing for sample {sample_id}")
                    fallback_count += 1
                    continue

            img_path = Path(img_path_str)
            if not img_path.exists():
                log_fallback_event(f"Image file not found: {img_path}")
                fallback_count += 1
                continue

            status, detections, recall = run_object_detection(model, sample, img_path)
            
            # Log status
            log_detection_status(sample.get('id', 'unknown'), status, len(detections))
            
            if status == 'success':
                success_count += 1
                if recall is not None:
                    recall_values.append(recall)
                    gt_present_count += 1
            elif status == 'zero_detection':
                zero_detection_count += 1
            else:
                fallback_count += 1

            # If GT was missing, log N/A
            if not check_ground_truth_exists(sample):
                gt_missing_count += 1
                if recall is None:
                    # Explicitly log N/A for recall
                    pass

    # Calculate final metrics
    overall_recall = None
    if gt_present_count > 0:
        overall_recall = sum(recall_values) / len(recall_values)
    
    results = {
        "total_samples": total_samples,
        "detection_status_counts": {
            "success": success_count,
            "zero_detection": zero_detection_count,
            "fallback": fallback_count
        },
        "ground_truth_stats": {
            "present": gt_present_count,
            "missing": gt_missing_count
        },
        "object_detection_recall": {
            "value": overall_recall,
            "count": gt_present_count,
            "status": "CALCULATED" if overall_recall is not None else "N/A"
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    return results

def main():
    """
    Main entry point for T011.
    Runs detection and writes results to data/processed/metrics/detection_recall.json
    """
    try:
        results = process_dataset_for_detection()
        
        output_path = DATA_PROCESSED_PATH / "detection_recall.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Detection results written to {output_path}")
        print(f"Overall Recall: {results['object_detection_recall']}")
        
    except Exception as e:
        print(f"Error during detection pipeline: {str(e)}")
        # Log the error but don't crash the whole script if possible
        # In a real CI, this might be a failure
        raise e

if __name__ == "__main__":
    main()