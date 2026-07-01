import os
import json
import math
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Attempt to import torch and torchvision, but allow graceful degradation if missing
# for the specific logging task if data is already pre-computed, though the task
# implies running the validation.
try:
    import torch
    import torchvision.models as models
    import torchvision.transforms as transforms
    from PIL import Image
    import numpy as np
except ImportError:
    warnings.warn("PyTorch or torchvision not installed. Validation logic requires them.")
    torch = None
    Image = None
    np = None

from src.config import get_config

@dataclass
class ValidationResult:
    image_id: str
    auc_score: float
    passed_threshold: bool
    model_name: str
    threshold: float
    timestamp: str
    details: Optional[Dict[str, Any]] = None

def load_salicon_test_set(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Loads the SALICON test set metadata or a subset for validation.
    In a real scenario, this would parse the SALICON JSON manifest.
    For this implementation, we assume the data exists in data/raw/salicon or similar.
    """
    # This is a placeholder logic to identify the data source.
    # In a full pipeline, T009 would have downloaded this.
    # We look for a manifest or a specific directory structure.
    salicon_path = Path(config['paths']['raw_data']) / 'salicon'
    manifest_path = salicon_path / 'salicon_test_set_manifest.json'
    
    if not manifest_path.exists():
        # If manifest doesn't exist, try to find images and generate IDs
        # This handles the case where raw download happened but manifest wasn't created
        images_dir = salicon_path / 'images'
        if images_dir.exists():
            images = [f for f in images_dir.iterdir() if f.suffix in ['.jpg', '.png', '.jpeg']]
            return [{'image_id': f.stem, 'path': str(f)} for f in images]
        else:
            raise FileNotFoundError("SALICON dataset not found in configured path.")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def load_fixation_map(image_id: str, config: Dict[str, Any]) -> np.ndarray:
    """
    Loads the ground truth fixation map for a given image ID from SALICON.
    Returns a normalized fixation map (0-1).
    """
    salicon_path = Path(config['paths']['raw_data']) / 'salicon'
    # Assumed structure: salicon/fixations/{image_id}.png or similar
    # SALICON usually provides fixation maps as PNGs with specific encoding
    # or as heatmaps. We assume a standard location.
    fixation_path = salicon_path / 'fixations' / f"{image_id}.png"
    
    if not fixation_path.exists():
        # Fallback search
        fixation_path = salicon_path / 'saliency_maps' / f"{image_id}.png"
    
    if not fixation_path.exists():
        raise FileNotFoundError(f"Fixation map not found for {image_id}")
    
    img = Image.open(fixation_path).convert('L') # Grayscale
    return np.array(img).astype(np.float32) / 255.0

def compute_auc(prediction_map: np.ndarray, ground_truth_map: np.ndarray) -> float:
    """
    Computes the Area Under the Curve (AUC-Judd) metric.
    prediction_map: Model's predicted saliency map (normalized 0-1)
    ground_truth_map: Human fixation map (normalized 0-1)
    """
    if prediction_map.shape != ground_truth_map.shape:
        # Resize prediction to match ground truth if necessary
        from PIL import Image
        pred_pil = Image.fromarray((prediction_map * 255).astype(np.uint8))
        gt_pil = Image.fromarray((ground_truth_map * 255).astype(np.uint8))
        # Simple resize if shapes mismatch
        pred_pil = pred_pil.resize(ground_truth_map.shape[::-1], Image.BILINEAR)
        prediction_map = np.array(pred_pil).astype(np.float32) / 255.0

    # Flatten maps
    pred_flat = prediction_map.flatten()
    gt_flat = ground_truth_map.flatten()

    # Threshold ground truth to get binary fixations (1 if fixation present)
    # Assuming values > 0.5 indicate a fixation in the normalized map
    binary_gt = (gt_flat > 0.5).astype(int)

    if np.sum(binary_gt) == 0:
        return 0.0

    # Sort predictions in descending order
    sorted_indices = np.argsort(pred_flat)[::-1]
    sorted_pred = pred_flat[sorted_indices]
    sorted_gt = binary_gt[sorted_indices]

    # Calculate TPR and FPR
    # TPR: True Positive Rate (Sensitivity)
    # FPR: False Positive Rate (1 - Specificity)
    # Since we are using a threshold on the prediction, we iterate through unique prediction values
    unique_preds = np.unique(sorted_pred)[::-1]
    
    tpr_list = []
    fpr_list = []
    
    total_pos = np.sum(sorted_gt)
    total_neg = len(sorted_gt) - total_pos

    current_pos = 0
    current_neg = 0

    # Calculate AUC using trapezoidal rule
    auc = 0.0
    prev_fpr = 0.0
    prev_tpr = 0.0

    for threshold in unique_preds:
        mask = sorted_pred >= threshold
        tp = np.sum(sorted_gt[mask])
        fp = np.sum((1 - sorted_gt)[mask])

        current_pos += tp
        current_neg += fp

        tpr = current_pos / total_pos if total_pos > 0 else 0
        fpr = current_neg / total_neg if total_neg > 0 else 0

        # Trapezoidal integration
        auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0
        prev_fpr = fpr
        prev_tpr = tpr

    return auc

def load_resnet18_saliency_model(config: Dict[str, Any]):
    """
    Loads the ResNet18 model for saliency map generation (CPU only).
    """
    if torch is None:
        raise ImportError("PyTorch is required for saliency model loading.")
    
    device = torch.device('cpu')
    model = models.resnet18(pretrained=True)
    model.eval()
    model.to(device)
    
    # Remove classification layer to use features
    # For saliency, we usually use the last conv layer
    return model, device

def generate_saliency_map(image_path: str, model, device, config: Dict[str, Any]) -> np.ndarray:
    """
    Generates a saliency map for a given image using the loaded model.
    """
    if torch is None:
        raise ImportError("PyTorch is required.")
    
    from PIL import Image
    import torchvision.transforms as transforms

    # Load and preprocess image
    img = Image.open(image_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    input_tensor = transform(img).unsqueeze(0).to(device)
    
    # Forward pass
    model.zero_grad()
    features = model(input_tensor)
    
    # For a simple saliency map without GradCAM implementation here,
    # we can use the sum of feature maps or a simple gradient-based approach.
    # However, T021/T022 imply the model is already set up.
    # We will simulate a basic saliency map based on feature magnitude for this task
    # if a full GradCAM is not explicitly implemented in the provided snippet.
    # But to be robust, let's assume we use the last conv layer output.
    
    # Since we stripped the classifier, we need to hook into the conv layers.
    # For simplicity in this specific task (logging results), we assume the model
    # produces a feature map that we can average.
    # A real implementation would use hooks.
    
    # Fallback: Return a random map if model is just a classifier? No, must be real.
    # Let's implement a simple gradient-based saliency.
    input_tensor.requires_grad = True
    output = model(input_tensor)
    # Assume we want to maximize the first class or sum of features
    # Since we don't have classes, we sum the output features
    loss = output.sum()
    loss.backward()
    
    gradients = input_tensor.grad.data.cpu().numpy()[0]
    # Take absolute value and max over channels
    saliency = np.max(np.abs(gradients), axis=0)
    
    # Resize to original image size if needed, but here we compare to GT which is resized
    # Normalize to 0-1
    saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)
    
    return saliency

def validate_single_image(image_id: str, config: Dict[str, Any]) -> ValidationResult:
    """
    Validates a single image from SALICON against the saliency model.
    """
    salicon_path = Path(config['paths']['raw_data']) / 'salicon'
    images_dir = salicon_path / 'images'
    image_path = images_dir / f"{image_id}.jpg"
    
    if not image_path.exists():
        image_path = images_dir / f"{image_id}.png"
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image {image_id} not found")

    # Load model
    model, device = load_resnet18_saliency_model(config)
    
    # Generate Saliency Map
    pred_map = generate_saliency_map(str(image_path), model, device, config)
    
    # Load Ground Truth
    gt_map = load_fixation_map(image_id, config)
    
    # Resize pred_map to match gt_map if necessary
    if pred_map.shape != gt_map.shape:
        from PIL import Image
        pred_pil = Image.fromarray((pred_map * 255).astype(np.uint8))
        pred_pil = pred_pil.resize(gt_map.shape[::-1], Image.BILINEAR)
        pred_map = np.array(pred_pil).astype(np.float32) / 255.0

    # Compute AUC
    auc_score = compute_auc(pred_map, gt_map)
    
    threshold = config['thresholds']['saliency_auc_threshold']
    passed = auc_score >= threshold

    return ValidationResult(
        image_id=image_id,
        auc_score=float(auc_score),
        passed_threshold=passed,
        model_name="resnet18_cpu",
        threshold=float(threshold),
        timestamp=datetime.now().isoformat(),
        details={"image_path": str(image_path)}
    )

def run_saliency_validation(config: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Runs the validation pipeline on the SALICON test set.
    """
    dataset = load_salicon_test_set(config)
    if limit:
        dataset = dataset[:limit]
    
    results = []
    for item in dataset:
        image_id = item['image_id']
        try:
            result = validate_single_image(image_id, config)
            results.append(asdict(result))
        except Exception as e:
            logging.error(f"Failed to validate {image_id}: {e}")
            results.append({
                "image_id": image_id,
                "auc_score": -1.0,
                "passed_threshold": False,
                "error": str(e)
            })
    
    return results

def main():
    """
    Main entry point for T023: Log validation results.
    """
    config = get_config()
    
    # Run validation
    results = run_saliency_validation(config)
    
    # Calculate aggregate stats
    valid_results = [r for r in results if r.get('auc_score', -1) >= 0]
    if valid_results:
        avg_auc = sum(r['auc_score'] for r in valid_results) / len(valid_results)
        passed_count = sum(1 for r in valid_results if r['passed_threshold'])
        total_count = len(valid_results)
    else:
        avg_auc = 0.0
        passed_count = 0
        total_count = 0

    output_data = {
        "status": "completed",
        "dataset": "SALICON",
        "model": "ResNet18 (CPU)",
        "total_images_validated": total_count,
        "average_auc": avg_auc,
        "threshold": config['thresholds']['saliency_auc_threshold'],
        "passed_count": passed_count,
        "failure_count": total_count - passed_count,
        "individual_results": results
    }

    output_path = Path(config['paths']['processed_data']) / 'saliency_validation.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Validation results written to {output_path}")
    print(f"Average AUC: {avg_auc:.4f} (Threshold: {config['thresholds']['saliency_auc_threshold']})")

if __name__ == "__main__":
    main()
