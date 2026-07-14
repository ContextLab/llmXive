"""
T029: Grad-CAM Visualization Generator.

Generates Grad-CAM heatmaps for model interpretability.
Outputs heatmaps to results/grad_cam_heatmaps/ for use by T030.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import torch
import torch.nn as nn
import cv2
from torchvision import models

from utils.config import get_project_root, get_data_dir, get_processed_dir, get_results_dir
from utils.logging_config import get_logger
from data.loader import MicrostructureDataset, OOMSafeDataLoader
from models.cnn import MaterialStrengthCNN, get_model


class GradCAM:
    """Grad-CAM implementation for extracting attention maps."""

    def __init__(self, model: nn.Module, target_layer: str):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        # Register hooks
        self._register_hooks()

    def _register_hooks(self):
        """Register forward and backward hooks for the target layer."""
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        target_module = None
        for name, module in self.model.named_modules():
            if name == self.target_layer:
                target_module = module
                break

        if target_module is None:
            raise ValueError(f"Target layer '{self.target_layer}' not found in model")

        self.forward_hook = target_module.register_forward_hook(forward_hook)
        self.backward_hook = target_module.register_full_backward_hook(backward_hook)

    def _generate_cam(self, target_class: int) -> np.ndarray:
        """Generate CAM for a target class."""
        # Zero out gradients
        if self.gradients is not None:
            self.gradients.zero_()

        # Forward pass
        self.model.eval()
        output = self.model(torch.tensor([target_class]))

        # Backward pass
        output.backward()

        if self.gradients is None or self.activations is None:
            return None

        # Get gradients and activations
        gradients = self.gradients.cpu().data.numpy()
        activations = self.activations.cpu().data.numpy()

        # Global average pooling over spatial dimensions
        weights = np.mean(gradients, axis=(2, 3), keepdims=True)

        # Generate CAM
        cam = np.sum(weights * activations, axis=1)
        cam = np.maximum(cam, 0)  # ReLU

        # Normalize
        cam = cam - np.min(cam)
        if np.max(cam) > 0:
            cam = cam / np.max(cam)

        return cam[0]  # Return single channel

    def __call__(self, x: torch.Tensor) -> np.ndarray:
        """Generate Grad-CAM heatmap for input."""
        self.model.eval()

        with torch.no_grad():
            # Get prediction
            output = self.model(x)
            target_class = output.argmax(dim=1).item()

        # Generate CAM
        cam = self._generate_cam(target_class)

        if cam is None:
            return None

        return cam

    def remove_hooks(self):
        """Remove registered hooks."""
        self.forward_hook.remove()
        self.backward_hook.remove()


def apply_grad_cam(
    model: nn.Module,
    image: torch.Tensor,
    target_layer: str = "features.18"
) -> Optional[np.ndarray]:
    """
    Apply Grad-CAM to an image.

    Args:
        model: Trained CNN model
        image: Input image tensor (1, C, H, W)
        target_layer: Name of the target layer for Grad-CAM

    Returns:
        Grad-CAM heatmap as numpy array (H, W), or None if failed.
    """
    try:
        grad_cam = GradCAM(model, target_layer)
        heatmap = grad_cam(image)
        grad_cam.remove_hooks()
        return heatmap
    except Exception as e:
        logging.warning(f"Grad-CAM failed: {e}")
        return None


def overlay_heatmap(
    image: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.5
) -> np.ndarray:
    """
    Overlay Grad-CAM heatmap on original image.

    Args:
        image: Original image (H, W, C) or (H, W)
        heatmap: Grad-CAM heatmap (H, W)
        alpha: Transparency of heatmap overlay

    Returns:
        Overlaid image (H, W, 3)
    """
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Resize heatmap to match image
    heatmap_resized = cv2.resize(heatmap, (image.shape[1], image.shape[0]))

    # Apply colormap
    heatmap_colored = cv2.applyColorMap((heatmap_resized * 255).astype(np.uint8), cv2.COLORMAP_JET)

    # Overlay
    overlay = (alpha * heatmap_colored + (1 - alpha) * image).astype(np.uint8)

    return overlay


def generate_grad_cam_visualization(
    model: nn.Module,
    image_path: Path,
    output_path: Path,
    target_layer: str = "features.18",
    save_heatmap_only: bool = False
) -> bool:
    """
    Generate Grad-CAM visualization for a single image.

    Args:
        model: Trained CNN model
        image_path: Path to input image
        output_path: Path to save output
        target_layer: Target layer for Grad-CAM
        save_heatmap_only: If True, save only heatmap (no overlay)

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Load image
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            logging.warning(f"Could not load image: {image_path}")
            return False

        # Preprocess
        image_tensor = torch.tensor(image, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        # Normalize if needed (assuming model expects normalized input)
        image_tensor = image_tensor / 255.0

        # Generate heatmap
        heatmap = apply_grad_cam(model, image_tensor, target_layer)

        if heatmap is None:
            return False

        if save_heatmap_only:
            # Save heatmap as numpy
            np.save(str(output_path.with_suffix('.npy')), heatmap)
        else:
            # Create overlay
            overlay = overlay_heatmap(image, heatmap)
            cv2.imwrite(str(output_path), overlay)

        return True
    except Exception as e:
        logging.warning(f"Failed to generate Grad-CAM for {image_path}: {e}")
        return False


def main():
    """Main entry point for Grad-CAM generation."""
    parser = argparse.ArgumentParser(description="Generate Grad-CAM visualizations")
    parser.add_argument("--model_path", type=str, required=True, help="Path to trained model")
    parser.add_argument("--manifest", type=str, required=True, help="Path to test set manifest")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for heatmaps")
    parser.add_argument("--target_layer", type=str, default="features.18", help="Target layer for Grad-CAM")
    parser.add_argument("--sample_size", type=int, default=10, help="Number of samples to process")
    args = parser.parse_args()

    # Setup logging
    logger = get_logger(__name__)

    # Get paths
    project_root = get_project_root()
    results_dir = get_results_dir()

    output_dir = Path(args.output_dir) if args.output_dir else (results_dir / "grad_cam_heatmaps")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Grad-CAM generation")
    logger.info(f"Model: {args.model_path}")
    logger.info(f"Output: {output_dir}")

    # Load model
    try:
        model = get_model()
        model.load_state_dict(torch.load(args.model_path, map_location='cpu'))
        model.eval()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return 1

    # Load manifest
    try:
        with open(args.manifest, 'r') as f:
            manifest = json.load(f)
        test_images = manifest.get('test', [])
        logger.info(f"Found {len(test_images)} test images in manifest")
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return 1

    # Process images
    success_count = 0
    for i, item in enumerate(test_images[:args.sample_size]):
        image_path = Path(item['image_path'])
        image_id = item.get('image_id', image_path.stem)

        output_path = output_dir / f"{image_id}_gradcam.png"

        if generate_grad_cam_visualization(
            model,
            image_path,
            output_path,
            args.target_layer,
            save_heatmap_only=False
        ):
            success_count += 1
            logger.info(f"Generated heatmap for {image_id}")
        else:
            logger.warning(f"Failed to generate heatmap for {image_id}")

    logger.info(f"Grad-CAM generation complete: {success_count}/{args.sample_size} successful")

    # Also save heatmaps as numpy for IoU calculation
    logger.info("Generating numpy heatmaps for IoU calculation...")
    for i, item in enumerate(test_images[:args.sample_size]):
        image_id = item.get('image_id', Path(item['image_path']).stem)
        png_path = output_dir / f"{image_id}_gradcam.png"

        if png_path.exists():
            heatmap = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
            if heatmap is not None:
                heatmap = heatmap.astype(np.float32) / 255.0
                npy_path = output_dir / f"{image_id}_gradcam.npy"
                np.save(str(npy_path), heatmap)

    return 0


if __name__ == "__main__":
    exit(main())
