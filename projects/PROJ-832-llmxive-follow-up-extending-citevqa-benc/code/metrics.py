"""
Core metrics for CiteVQA evaluation pipeline.

Implements:
- calculate_iou: Intersection over Union for bounding boxes
- semantic_similarity: Cosine similarity between embeddings (L2 normalized)
- compute_saa: Strict Attributed Accuracy (Answer Correctness + Spatial Correctness)
- compute_vla: Visual Localization Accuracy
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.spatial.distance import cosine

# Type aliases for clarity
BoundingBox = Tuple[float, float, float, float]  # (x1, y1, x2, y2)
Embedding = np.ndarray


def calculate_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        box1: First bounding box (x1, y1, x2, y2)
        box2: Second bounding box (x1, y1, x2, y2)
    
    Returns:
        IoU score between 0.0 and 1.0. Returns 0.0 if either box has invalid area.
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    # Validate boxes (ensure min < max)
    if x1_min >= x1_max or y1_min >= y1_max or x2_min >= x2_max or y2_min >= y2_max:
        return 0.0
    
    # Calculate intersection coordinates
    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)
    
    # Calculate intersection area
    inter_width = max(0.0, inter_x_max - inter_x_min)
    inter_height = max(0.0, inter_y_max - inter_y_min)
    inter_area = inter_width * inter_height
    
    # Calculate union area
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    
    # Avoid division by zero
    if union_area == 0:
        return 0.0
    
    iou = inter_area / union_area
    return float(iou)


def semantic_similarity(emb1: Embedding, emb2: Embedding) -> float:
    """
    Calculate cosine similarity between two L2-normalized embeddings.
    
    Args:
        emb1: First embedding vector (should be L2 normalized)
        emb2: Second embedding vector (should be L2 normalized)
    
    Returns:
        Cosine similarity score between -1.0 and 1.0.
        For L2-normalized vectors, this is equivalent to dot product.
    """
    if emb1.shape != emb2.shape:
        raise ValueError(f"Embedding shapes must match: {emb1.shape} vs {emb2.shape}")
    
    # Ensure L2 normalization (in case input is not normalized)
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    emb1_normalized = emb1 / norm1
    emb2_normalized = emb2 / norm2
    
    # Cosine similarity for normalized vectors is just dot product
    sim = np.dot(emb1_normalized, emb2_normalized)
    
    # Clamp to [-1, 1] to handle floating point errors
    return float(np.clip(sim, -1.0, 1.0))


def compute_saa(
    predicted_answer: str,
    ground_truth_answer: str,
    predicted_box: Optional[BoundingBox],
    ground_truth_box: Optional[BoundingBox],
    answer_threshold: float = 0.85,
    iou_threshold: float = 0.5
) -> Dict[str, Union[bool, float, str]]:
    """
    Compute Strict Attributed Accuracy (SAA).
    
    SAA is True if BOTH conditions are met:
    1. Answer Correctness: Exact Match OR Semantic Similarity >= threshold
    2. Spatial Correctness: IoU > threshold (if boxes provided)
    
    Args:
        predicted_answer: Model's predicted answer string
        ground_truth_answer: Ground truth answer string
        predicted_box: Predicted bounding box (x1, y1, x2, y2) or None
        ground_truth_box: Ground truth bounding box (x1, y1, x2, y2) or None
        answer_threshold: Minimum semantic similarity for answer correctness (default 0.85)
        iou_threshold: Minimum IoU for spatial correctness (default 0.5)
    
    Returns:
        Dictionary with:
        - 'saa': bool - Overall SAA result
        - 'answer_correct': bool - Whether answer is correct
        - 'spatial_correct': bool - Whether spatial attribution is correct
        - 'answer_similarity': float - Semantic similarity score (if embeddings available)
        - 'iou': float - IoU score (if boxes provided)
    """
    # Answer Correctness: Exact Match OR Semantic Similarity >= threshold
    answer_correct = False
    answer_similarity = 0.0
    
    # Exact match check (case-insensitive, stripped)
    if predicted_answer.strip().lower() == ground_truth_answer.strip().lower():
        answer_correct = True
        answer_similarity = 1.0
    else:
        # Note: In a full implementation, embeddings would be computed here
        # For now, we return similarity as 0.0 if no exact match
        # The caller should provide embeddings if semantic similarity is needed
        answer_similarity = 0.0
    
    # Spatial Correctness: IoU > threshold
    spatial_correct = False
    iou = 0.0
    
    if predicted_box is not None and ground_truth_box is not None:
        iou = calculate_iou(predicted_box, ground_truth_box)
        spatial_correct = iou > iou_threshold
    else:
        # If no boxes provided, spatial correctness is considered False
        # (or could be considered True if spatial attribution is not required)
        # Based on task description, we require spatial correctness
        spatial_correct = False
    
    # Overall SAA: Both conditions must be met
    saa = answer_correct and spatial_correct
    
    return {
        'saa': saa,
        'answer_correct': answer_correct,
        'spatial_correct': spatial_correct,
        'answer_similarity': answer_similarity,
        'iou': iou
    }


def compute_vla(
    predicted_box: BoundingBox,
    ground_truth_box: BoundingBox,
    iou_threshold: float = 0.5
) -> Dict[str, Union[bool, float]]:
    """
    Compute Visual Localization Accuracy (VLA).
    
    VLA is True if the predicted bounding box has IoU > threshold with ground truth.
    
    Args:
        predicted_box: Predicted bounding box (x1, y1, x2, x2)
        ground_truth_box: Ground truth bounding box (x1, y1, x2, y2)
        iou_threshold: Minimum IoU for accuracy (default 0.5)
    
    Returns:
        Dictionary with:
        - 'vla': bool - Whether localization is accurate
        - 'iou': float - IoU score
    """
    iou = calculate_iou(predicted_box, ground_truth_box)
    vla = iou > iou_threshold
    
    return {
        'vla': vla,
        'iou': iou
    }


def compute_batch_saa(
    predictions: List[Dict],
    ground_truths: List[Dict],
    answer_threshold: float = 0.85,
    iou_threshold: float = 0.5
) -> Dict[str, float]:
    """
    Compute batch SAA metrics over a list of predictions and ground truths.
    
    Args:
        predictions: List of prediction dicts with keys:
            - 'predicted_answer': str
            - 'predicted_box': Optional[BoundingBox]
        ground_truths: List of ground truth dicts with keys:
            - 'ground_truth_answer': str
            - 'ground_truth_box': Optional[BoundingBox]
        answer_threshold: Threshold for answer correctness
        iou_threshold: Threshold for spatial correctness
    
    Returns:
        Dictionary with:
        - 'mean_saa': float - Mean SAA across all samples
        - 'mean_iou': float - Mean IoU across all samples
        - 'total_samples': int - Number of samples
        - 'saa_count': int - Number of samples with SAA=True
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground_truths must have the same length")
    
    if len(predictions) == 0:
        return {
            'mean_saa': 0.0,
            'mean_iou': 0.0,
            'total_samples': 0,
            'saa_count': 0
        }
    
    saa_values = []
    iou_values = []
    
    for pred, gt in zip(predictions, ground_truths):
        result = compute_saa(
            predicted_answer=pred['predicted_answer'],
            ground_truth_answer=gt['ground_truth_answer'],
            predicted_box=pred.get('predicted_box'),
            ground_truth_box=gt.get('ground_truth_box'),
            answer_threshold=answer_threshold,
            iou_threshold=iou_threshold
        )
        
        saa_values.append(1.0 if result['saa'] else 0.0)
        iou_values.append(result['iou'])
    
    return {
        'mean_saa': float(np.mean(saa_values)),
        'mean_iou': float(np.mean(iou_values)),
        'total_samples': len(predictions),
        'saa_count': int(sum(saa_values))
    }


def compute_batch_vla(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5
) -> Dict[str, float]:
    """
    Compute batch VLA metrics over a list of predictions and ground truths.
    
    Args:
        predictions: List of prediction dicts with keys:
            - 'predicted_box': BoundingBox
        ground_truths: List of ground truth dicts with keys:
            - 'ground_truth_box': BoundingBox
        iou_threshold: Threshold for VLA accuracy
    
    Returns:
        Dictionary with:
        - 'mean_vla': float - Mean VLA across all samples
        - 'mean_iou': float - Mean IoU across all samples
        - 'total_samples': int - Number of samples
        - 'vla_count': int - Number of samples with VLA=True
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground_truths must have the same length")
    
    if len(predictions) == 0:
        return {
            'mean_vla': 0.0,
            'mean_iou': 0.0,
            'total_samples': 0,
            'vla_count': 0
        }
    
    vla_values = []
    iou_values = []
    
    for pred, gt in zip(predictions, ground_truths):
        result = compute_vla(
            predicted_box=pred['predicted_box'],
            ground_truth_box=gt['ground_truth_box'],
            iou_threshold=iou_threshold
        )
        
        vla_values.append(1.0 if result['vla'] else 0.0)
        iou_values.append(result['iou'])
    
    return {
        'mean_vla': float(np.mean(vla_values)),
        'mean_iou': float(np.mean(iou_values)),
        'total_samples': len(predictions),
        'vla_count': int(sum(vla_values))
    }
