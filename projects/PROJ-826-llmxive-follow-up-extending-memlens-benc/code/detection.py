import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import logging

# Attempt to import ultralytics; if missing, we will handle the error gracefully
# but the code will fail loudly if the dependency is not installed, as per constraints.
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None

from utils.logger import get_detection_logger, log_detection_status, log_fallback_event

# Configuration paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "memlens"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
METRICS_DIR = PROCESSED_DATA_PATH / "metrics"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
METRICS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# YOLO Model Configuration
YOLO_MODEL_NAME = "yolov8n.pt"  # Using 'nano' (n) as the tiny equivalent for CPU efficiency
YOLO_CONF_THRESHOLD = 0.25
YOLO_IOU_THRESHOLD = 0.45

def load_yolo_model(model_name: str = YOLO_MODEL_NAME) -> Optional[object]:
    """
    Loads the YOLOv8 model.
    Returns None if the model cannot be loaded or ultralytics is not installed.
    """
    if not YOLO_AVAILABLE:
        logger = get_detection_logger()
        logger.error("Ultralytics library not found. Please install it via requirements.txt.")
        return None

    try:
        logger = get_detection_logger()
        logger.info(f"Loading YOLO model: {model_name}")
        model = YOLO(model_name)
        logger.info("YOLO model loaded successfully.")
        return model
    except Exception as e:
        logger = get_detection_logger()
        logger.error(f"Failed to load YOLO model: {e}")
        log_fallback_event("YOLO_LOAD_FAILURE", str(e))
        return None

def check_ground_truth_exists(sample_data: Dict[str, Any]) -> bool:
    """
    Checks if ground truth bounding boxes exist for a given sample.
    MemLens dataset structure usually includes 'annotations' or 'gt_boxes'.
    """
    # Check for common keys in MemLens-like structures
    if 'annotations' in sample_data and sample_data['annotations']:
        # Check if any annotation has a bbox
        for ann in sample_data['annotations']:
            if 'bbox' in ann and ann['bbox'] and len(ann['bbox']) == 4:
                return True
    if 'gt_boxes' in sample_data and sample_data['gt_boxes']:
        return True
    if 'bboxes' in sample_data and sample_data['bboxes']:
        return True
    
    return False

def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculates Intersection over Union (IoU) between two boxes.
    box format: [x_min, y_min, x_max, y_max]
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

def run_object_detection(model: object, image_path: str) -> Tuple[List[Dict], str]:
    """
    Runs YOLO detection on a single image.
    Returns (detections_list, status)
    status: 'success', 'zero_detection', 'fallback'
    """
    if not model:
        return [], "fallback"

    logger = get_detection_logger()
    try:
        results = model(image_path, conf=YOLO_CONF_THRESHOLD, iou=YOLO_IOU_THRESHOLD, verbose=False)
        
        # Extract boxes and confidence
        # results[0].boxes.xyxy -> tensor
        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            scores = results[0].boxes.conf.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy()
            
            detections = []
            for i, box in enumerate(boxes):
                detections.append({
                    "bbox": box.tolist(),
                    "confidence": float(scores[i]),
                    "class_id": int(classes[i])
                })
            
            if len(detections) > 0:
                return detections, "success"
            else:
                return [], "zero_detection"
        else:
            return [], "zero_detection"
    except Exception as e:
        logger.error(f"Error running detection on {image_path}: {e}")
        log_fallback_event("DETECTION_RUNTIME_ERROR", str(e))
        return [], "fallback"

def calculate_recall(detections: List[Dict], ground_truth_boxes: List[List[float]], iou_threshold: float = 0.5) -> float:
    """
    Calculates Recall = TP / (TP + FN)
    """
    if not ground_truth_boxes:
        return 0.0 # Should not happen if called correctly, but safety first
    
    tp = 0
    fn = 0
    matched_gt_indices = set()
    
    # Sort detections by confidence to prioritize high-confidence matches
    sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    
    for det in sorted_detections:
        det_box = det['bbox']
        best_iou = 0
        best_gt_idx = -1
        
        for gt_idx, gt_box in enumerate(ground_truth_boxes):
            if gt_idx in matched_gt_indices:
                continue
            iou = calculate_iou(det_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx
        
        if best_iou >= iou_threshold:
            tp += 1
            matched_gt_indices.add(best_gt_idx)
        # else: FP, ignored for recall calculation

    fn = len(ground_truth_boxes) - len(matched_gt_indices)
    
    if (tp + fn) == 0:
        return 0.0
    
    return tp / (tp + fn)

def process_dataset_for_detection(dataset_path: str, model: object) -> List[Dict]:
    """
    Iterates through the dataset, runs detection, and collects results.
    Assumes dataset_path points to a directory containing images and a JSON metadata file.
    """
    logger = get_detection_logger()
    results = []
    
    # Heuristic to find metadata file
    meta_file = None
    for f in os.listdir(dataset_path):
        if f.endswith('.json') and 'meta' in f.lower():
            meta_file = os.path.join(dataset_path, f)
            break
    
    if not meta_file:
        # Fallback: look for any json
        json_files = [f for f in os.listdir(dataset_path) if f.endswith('.json')]
        if json_files:
            meta_file = os.path.join(dataset_path, json_files[0])
    
    if not meta_file:
        logger.error("No metadata JSON file found in dataset directory.")
        return []

    with open(meta_file, 'r') as f:
        data = json.load(f)
    
    # Handle different dataset structures (list vs dict with key)
    samples = data if isinstance(data, list) else data.get('samples', data.get('data', []))
    
    if not samples:
        logger.warning("No samples found in metadata.")
        return []

    total_samples = len(samples)
    processed_count = 0
    
    for i, sample in enumerate(samples):
        logger.info(f"Processing sample {i+1}/{total_samples}")
        
        image_path = None
        if 'image_path' in sample:
            image_path = os.path.join(dataset_path, sample['image_path'])
        elif 'image' in sample:
            image_path = os.path.join(dataset_path, sample['image'])
        
        if not image_path or not os.path.exists(image_path):
            # Try to construct path if relative
            if image_path and not os.path.isabs(image_path):
                image_path = os.path.join(dataset_path, image_path)
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                continue

        gt_exists = check_ground_truth_exists(sample)
        gt_boxes = []
        
        if gt_exists:
            if 'annotations' in sample:
                gt_boxes = [ann['bbox'] for ann in sample['annotations'] if 'bbox' in ann]
            elif 'gt_boxes' in sample:
                gt_boxes = sample['gt_boxes']
            elif 'bboxes' in sample:
                gt_boxes = sample['bboxes']
        
        detections, status = run_object_detection(model, image_path)
        
        log_detection_status(status)
        
        recall = None
        if gt_exists:
            recall = calculate_recall(detections, gt_boxes)
        else:
            recall = "N/A"

        result_entry = {
            "sample_id": sample.get('id', i),
            "image_path": image_path,
            "detection_status": status,
            "detection_count": len(detections),
            "ground_truth_exists": gt_exists,
            "recall": recall,
            "detections": detections # Storing raw detections for debugging if needed
        }
        results.append(result_entry)
        processed_count += 1

    return results

def calculate_recall_statistics(results: List[Dict]) -> Dict[str, Any]:
    """
    Aggregates recall statistics from the processing results.
    Only considers samples where ground truth exists.
    """
    recalls = []
    for r in results:
        if r['ground_truth_exists'] and r['recall'] != "N/A":
            recalls.append(r['recall'])
    
    if not recalls:
        return {
            "total_samples": len(results),
            "samples_with_gt": 0,
            "mean_recall": 0.0,
            "min_recall": 0.0,
            "max_recall": 0.0,
            "status": "NO_GT_DATA"
        }
    
    mean_recall = float(np.mean(recalls))
    min_recall = float(np.min(recalls))
    max_recall = float(np.max(recalls))
    
    return {
        "total_samples": len(results),
        "samples_with_gt": len(recalls),
        "mean_recall": mean_recall,
        "min_recall": min_recall,
        "max_recall": max_recall,
        "status": "SUCCESS"
    }

def main():
    logger = get_detection_logger()
    logger.info("Starting Object Detection Pipeline (T011)")
    
    # Check if data exists
    if not RAW_DATA_PATH.exists():
        logger.error(f"Raw data path not found: {RAW_DATA_PATH}. Run T004 first.")
        return

    # Load Model
    model = load_yolo_model()
    if not model:
        logger.error("Failed to load YOLO model. Aborting.")
        return

    # Process Dataset
    results = process_dataset_for_detection(str(RAW_DATA_PATH), model)
    
    if not results:
        logger.warning("No results generated.")
        return

    # Calculate Statistics
    stats = calculate_recall_statistics(results)
    
    # Prepare final output
    output_data = {
        "pipeline": "YOLOv8-Tiny Object Detection",
        "model": YOLO_MODEL_NAME,
        "statistics": stats,
        "detailed_results": results
    }
    
    # Write to disk
    output_path = METRICS_DIR / "detection_recall.json"
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Detection results written to {output_path}")
    logger.info(f"Mean Recall (GT samples): {stats['mean_recall']:.4f}")

if __name__ == "__main__":
    main()
