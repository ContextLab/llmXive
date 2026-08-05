import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from ultralytics import YOLO
import logging
from utils.logger import get_detection_logger, log_detection_status, log_fallback_event

# Constants
MODEL_NAME = "yolov8n.pt"  # YOLOv8 Nano (Tiny-equivalent for speed)
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45

def load_yolo_model(model_path: str = MODEL_NAME) -> YOLO:
    """
    Load the YOLOv8 model.
    """
    logger = get_detection_logger()
    logger.info(f"Loading YOLO model: {model_path}")
    try:
        model = YOLO(model_path)
        logger.info("YOLO model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")
        raise

def check_ground_truth_exists(sample: Dict[str, Any]) -> bool:
    """
    Check if the sample contains ground truth bounding boxes.
    Expected structure: sample.get('annotations', []) or sample.get('ground_truth', {}).get('bboxes', [])
    Adapt based on actual MemLens dataset structure.
    """
    # Attempt common keys found in MemLens or similar datasets
    if 'annotations' in sample and len(sample['annotations']) > 0:
        # Check if annotations contain bbox info
        first_ann = sample['annotations'][0]
        if 'bbox' in first_ann or 'bbox_points' in first_ann:
            return True
    
    if 'ground_truth' in sample:
        gt = sample['ground_truth']
        if isinstance(gt, dict):
            if 'bboxes' in gt and len(gt['bboxes']) > 0:
                return True
            if 'boxes' in gt and len(gt['boxes']) > 0:
                return True
    
    # Fallback check for raw list of boxes
    if 'bboxes' in sample and len(sample['bboxes']) > 0:
        return True

    return False

def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two boxes.
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

def run_object_detection(model: YOLO, image_path: str) -> Tuple[List[Dict], bool]:
    """
    Run YOLO object detection on a single image.
    Returns: (detections, success)
    detections: List of dicts with keys: 'class', 'bbox', 'confidence'
    success: True if model ran without error, False if fallback occurred
    """
    logger = get_detection_logger()
    try:
        # Run inference
        results = model(image_path, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD, verbose=False)
        
        detections = []
        if len(results) > 0:
            r = results[0]
            if r.boxes is not None:
                boxes = r.boxes.xyxy.cpu().numpy()
                confs = r.boxes.conf.cpu().numpy()
                cls_ids = r.boxes.cls.cpu().numpy()
                
                for i, box in enumerate(boxes):
                    detections.append({
                        'class': int(cls_ids[i]),
                        'bbox': box.tolist(), # [x_min, y_min, x_max, y_max]
                        'confidence': float(confs[i])
                    })
        
        logger.debug(f"Detection completed for {image_path}: {len(detections)} objects found")
        return detections, True

    except Exception as e:
        logger.error(f"YOLO detection failed for {image_path}: {e}")
        log_fallback_event(f"YOLO detection failed: {e}")
        return [], False

def calculate_recall(detections: List[Dict], ground_truths: List[Dict], iou_thresh: float = 0.5) -> float:
    """
    Calculate Object Detection Recall: TP / (TP + FN)
    ground_truths: List of dicts with 'bbox' key
    detections: List of dicts with 'bbox' key
    """
    if not ground_truths:
        return 0.0 # Should be handled by caller (N/A case), but safe fallback

    tp = 0
    matched_gt_indices = set()

    for det in detections:
        det_box = det['bbox']
        best_iou = 0.0
        best_gt_idx = -1

        for idx, gt in enumerate(ground_truths):
            if idx in matched_gt_indices:
                continue
            gt_box = gt['bbox']
            iou = calculate_iou(det_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = idx

        if best_iou >= iou_thresh:
            tp += 1
            matched_gt_indices.add(best_gt_idx)

    fn = len(ground_truths) - len(matched_gt_indices)
    denominator = tp + fn
    
    if denominator == 0:
        return 0.0
    
    return tp / denominator

def process_dataset_for_detection(dataset_path: str, output_path: str) -> Dict[str, Any]:
    """
    Process the entire dataset to run object detection and calculate recall.
    """
    logger = get_detection_logger()
    logger.info(f"Starting dataset processing for detection: {dataset_path}")
    
    # Load dataset (assuming JSONL or JSON list format as per MemLens structure)
    # Adjust loader based on actual format from download.py
    data_path = Path(dataset_path)
    samples = []
    
    if data_path.suffix == '.jsonl':
        with open(data_path, 'r') as f:
            for line in f:
                samples.append(json.loads(line))
    elif data_path.suffix == '.json':
        with open(data_path, 'r') as f:
            data = json.load(f)
            samples = data if isinstance(data, list) else data.get('samples', [])
    else:
        # Fallback for directory of images if dataset is raw
        logger.error("Dataset format not supported. Expected .json or .jsonl")
        raise ValueError("Unsupported dataset format")

    model = load_yolo_model()
    
    total_tp = 0
    total_fn = 0
    total_samples = 0
    gt_exists_count = 0
    detection_results = []
    
    for idx, sample in enumerate(samples):
        image_path = sample.get('image_path') or sample.get('image')
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Image not found for sample {idx}: {image_path}")
            continue

        # Check GT
        has_gt = check_ground_truth_exists(sample)
        gt_boxes = []
        if has_gt:
            gt_exists_count += 1
            # Extract GT boxes based on common structures
            if 'annotations' in sample:
                gt_boxes = [ann['bbox'] for ann in sample['annotations'] if 'bbox' in ann]
            elif 'ground_truth' in sample:
                gt = sample['ground_truth']
                if 'bboxes' in gt:
                    gt_boxes = gt['bboxes']
                elif 'boxes' in gt:
                    gt_boxes = gt['boxes']
            elif 'bboxes' in sample:
                gt_boxes = sample['bboxes']
            
            # Normalize if needed (assuming pixel coordinates for now)
            # If GT is normalized [0-1], we might need image size to convert.
            # For now, assuming raw pixels or consistent format with YOLO output.

        # Run Detection
        detections, success = run_object_detection(model, image_path)
        
        status = 'success' if success and len(detections) > 0 else 'zero_detection' if success else 'fallback'
        
        recall = None
        if has_gt:
            recall = calculate_recall(detections, gt_boxes)
            total_tp += int(recall * len(gt_boxes)) # Approximate TP count
            total_fn += len(gt_boxes) - int(recall * len(gt_boxes))
            total_samples += 1
        
        result_entry = {
            'sample_id': sample.get('id', idx),
            'image_path': image_path,
            'detection_status': status,
            'num_detections': len(detections),
            'ground_truth_exists': has_gt,
            'recall': recall
        }
        
        if not success:
            log_fallback_event(f"Sample {idx}: {status}")
        
        detection_results.append(result_entry)
        logger.info(f"Processed sample {idx}: status={status}, recall={recall}")

    # Calculate Final Recall
    final_recall = 0.0
    if total_samples > 0:
        # Re-calculate strictly: TP / (TP + FN)
        # We need to re-iterate or store TP/FN per sample. 
        # Let's re-calculate from the stored results if possible, 
        # or just compute from the aggregates if we tracked TP/FN correctly.
        # Since calculate_recall returns a float, we can't easily sum them.
        # Let's assume we want the average recall over samples with GT.
        recalls = [r['recall'] for r in detection_results if r['recall'] is not None]
        if recalls:
            final_recall = sum(recalls) / len(recalls)
    
    metrics = {
        'total_samples_processed': len(detection_results),
        'samples_with_ground_truth': gt_exists_count,
        'object_detection_recall': final_recall,
        'status_distribution': {
            'success': sum(1 for r in detection_results if r['detection_status'] == 'success'),
            'zero_detection': sum(1 for r in detection_results if r['detection_status'] == 'zero_detection'),
            'fallback': sum(1 for r in detection_results if r['detection_status'] == 'fallback')
        },
        'results': detection_results
    }

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Detection results written to {output_path}")
    return metrics

def main():
    """
    Entry point for running the detection pipeline.
    """
    # Paths should be configured or passed via args
    # Defaulting to project structure
    base_dir = Path(__file__).parent.parent
    dataset_path = base_dir / "data" / "raw" / "memlens" / "processed" / "memlens_dataset.json" # Adjust based on actual download path
    output_path = base_dir / "data" / "processed" / "metrics" / "detection_recall.json"

    if not dataset_path.exists():
        # Try to find the actual downloaded file
        raw_dir = base_dir / "data" / "raw" / "memlens"
        if raw_dir.exists():
            for f in raw_dir.rglob("*.json"):
                if "memlens" in f.name:
                    dataset_path = f
                    break
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found at {dataset_path}. Please run download.py first.")

    process_dataset_for_detection(str(dataset_path), str(output_path))

if __name__ == "__main__":
    main()
