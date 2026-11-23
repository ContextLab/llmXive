"""
Grad-CAM Visualization Generator for Material Strength Prediction.

This module implements the Grad-CAM algorithm to generate heatmaps showing
which regions of the microstructure image contribute most to the CNN's
prediction of yield strength.

FR-006: Generate Grad-CAM heatmaps for model interpretability.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import models

# Import project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import (
    get_project_root,
    get_data_dir,
    get_processed_dir,
    get_results_dir,
    get_code_dir,
    set_seed,
    get_seed,
)
from data.loader import MicrostructureDataset
from models.cnn import MaterialStrengthCNN, get_model


def setup_logging() -> logging.Logger:
    """Configure logging for the interpret module."""
    logger = logging.getLogger("interpret")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class GradCAM:
    """
    Grad-CAM implementation for generating class activation maps.

    This class computes the gradient of the target output with respect to
    the feature maps of a specific layer to generate a heatmap indicating
    important regions.
    """

    def __init__(
        self,
        model: torch.nn.Module,
        target_layer_name: str = "features.18",
        device: Optional[torch.device] = None,
    ):
        """
        Initialize GradCAM.

        Args:
            model: The CNN model to analyze.
            target_layer_name: Name of the layer to extract gradients from.
                               For MobileNetV2, typically the last conv layer.
            device: Torch device to use.
        """
        self.model = model
        self.device = device or (
            torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        )
        self.target_layer_name = target_layer_name
        self.gradients: Optional[torch.Tensor] = None
        self.feature_maps: Optional[torch.Tensor] = None

        # Register hooks
        self._register_hooks()

    def _register_hooks(self) -> None:
        """Register forward and backward hooks to capture feature maps and gradients."""
        target_layer = None

        # Traverse the model to find the target layer
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                target_layer = module
                break

        if target_layer is None:
            # Fallback: try to find the last convolutional layer
            logging.warning(
                f"Target layer {self.target_layer_name} not found. "
                "Attempting to find last conv layer."
            )
            conv_layers = []
            for name, module in self.model.named_modules():
                if isinstance(module, torch.nn.Conv2d):
                    conv_layers.append((name, module))
            if conv_layers:
                target_layer_name, target_layer = conv_layers[-1]
                self.target_layer_name = target_layer_name
            else:
                raise ValueError("No convolutional layers found in the model.")

        def forward_hook(module, input, output):
            self.feature_maps = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        self.forward_hook_handle = target_layer.register_forward_hook(forward_hook)
        self.backward_hook_handle = target_layer.register_backward_hook(backward_hook)

    def generate_cam(
        self, input_tensor: torch.Tensor, target: Optional[torch.Tensor] = None
    ) -> np.ndarray:
        """
        Generate the Grad-CAM heatmap.

        Args:
            input_tensor: Input image tensor (B, C, H, W).
            target: Target tensor for backpropagation. If None, uses the model output.

        Returns:
            numpy array of the heatmap (H, W) normalized to [0, 1].
        """
        self.model.zero_grad()

        # Forward pass
        output = self.model(input_tensor)

        # If target is not provided, use the output for the predicted class
        if target is None:
            target = output

        # Backward pass
        target.backward(retain_graph=True)

        if self.gradients is None or self.feature_maps is None:
            raise RuntimeError("Hooks did not capture gradients or feature maps.")

        # Global average pooling of gradients
        gradients = self.gradients
        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)

        # Weighted combination of feature maps
        cam = torch.sum(weights * self.feature_maps, dim=1, keepdim=True)

        # ReLU to only keep positive contributions
        cam = F.relu(cam)

        # Resize to input image size
        cam = F.interpolate(
            cam,
            size=(input_tensor.shape[2], input_tensor.shape[3]),
            mode="bilinear",
            align_corners=False,
        )

        # Normalize to [0, 1]
        cam = cam - torch.min(cam)
        cam = cam / (torch.max(cam) + 1e-8)

        return cam.squeeze().cpu().numpy()

    def __del__(self):
        """Remove hooks when object is destroyed."""
        if hasattr(self, "forward_hook_handle"):
            self.forward_hook_handle.remove()
        if hasattr(self, "backward_hook_handle"):
            self.backward_hook_handle.remove()


def apply_grad_cam(
    model: torch.nn.Module,
    image_tensor: torch.Tensor,
    target_layer: str = "features.18",
    device: Optional[torch.device] = None,
) -> np.ndarray:
    """
    Apply Grad-CAM to a single image.

    Args:
        model: The trained CNN model.
        image_tensor: Input image tensor (1, C, H, W).
        target_layer: Name of the target layer.
        device: Torch device.

    Returns:
        Grad-CAM heatmap as a numpy array (H, W).
    """
    grad_cam = GradCAM(model, target_layer_name=target_layer, device=device)
    heatmap = grad_cam.generate_cam(image_tensor)
    return heatmap


def overlay_heatmap(
    image: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.5,
    colormap: str = "jet",
) -> np.ndarray:
    """
    Overlay a Grad-CAM heatmap onto the original image.

    Args:
        image: Original image (H, W, C) in uint8 [0, 255].
        heatmap: Heatmap (H, W) in float [0, 1].
        alpha: Transparency of the heatmap overlay.
        colormap: Matplotlib colormap name.

    Returns:
        Overlayed image (H, W, C) in uint8 [0, 255].
    """
    # Apply colormap
    if colormap == "jet":
        # Use OpenCV's applyColorMap which expects uint8 [0, 255]
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    else:
        # Fallback for other colormaps using matplotlib
        try:
            import matplotlib.cm as cm
            import matplotlib.colors as colors

            cmap = cm.get_cmap(colormap)
            heatmap_colored = (cmap(heatmap)[:, :, :3] * 255).astype(np.uint8)
            heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_RGB2BGR)
        except ImportError:
            # Fallback to simple red overlay if matplotlib is not available
            heatmap_colored = np.zeros_like(image)
            heatmap_colored[:, :, 2] = (heatmap * 255).astype(np.uint8)

    # Blend with original image
    image_float = image.astype(np.float32)
    heatmap_float = heatmap_colored.astype(np.float32)

    overlay = (1 - alpha) * image_float + alpha * heatmap_float
    overlay = np.clip(overlay, 0, 255).astype(np.uint8)

    return overlay


def generate_grad_cam_visualization(
    model: torch.nn.Module,
    image_path: Path,
    output_path: Path,
    device: Optional[torch.device] = None,
    target_layer: str = "features.18",
    alpha: float = 0.5,
    save_heatmap: bool = True,
) -> Dict[str, Any]:
    """
    Generate a Grad-CAM visualization for a single image.

    Args:
        model: Trained CNN model.
        image_path: Path to the input image.
        output_path: Path to save the overlayed image.
        device: Torch device.
        target_layer: Target layer name for Grad-CAM.
        alpha: Transparency for overlay.
        save_heatmap: Whether to save the raw heatmap as well.

    Returns:
        Dictionary with paths and metadata.
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Convert BGR to RGB for processing
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Preprocess image (resize if needed, though dataset should handle this)
    h, w = image_rgb.shape[:2]
    if h != 224 or w != 224:
        image_rgb = cv2.resize(image_rgb, (224, 224), interpolation=cv2.INTER_LINEAR)

    # Convert to tensor
    image_tensor = torch.from_numpy(image_rgb).permute(2, 0, 1).float() / 255.0
    image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension

    if device is None:
        device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    image_tensor = image_tensor.to(device)
    model = model.to(device)
    model.eval()

    # Generate heatmap
    with torch.no_grad():
        # We need gradients, so we wrap in torch.enable_grad
        image_tensor.requires_grad = True
        heatmap = apply_grad_cam(
            model, image_tensor, target_layer=target_layer, device=device
        )

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Overlay heatmap
    overlay = overlay_heatmap(image_rgb, heatmap, alpha=alpha)
    # Convert back to BGR for OpenCV saving
    overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(output_path), overlay_bgr)

    result = {
        "original_image": str(image_path),
        "overlay_image": str(output_path),
        "heatmap_shape": list(heatmap.shape),
        "heatmap_min": float(np.min(heatmap)),
        "heatmap_max": float(np.max(heatmap)),
        "heatmap_mean": float(np.mean(heatmap)),
    }

    # Save raw heatmap if requested
    if save_heatmap:
        heatmap_path = output_path.parent / (
            output_path.stem + "_heatmap.npy"
        )
        np.save(str(heatmap_path), heatmap)
        result["heatmap_file"] = str(heatmap_path)

    return result


def main():
    """
    Main entry point for Grad-CAM visualization generation.

    Usage:
        python code/eval/interpret.py --model-path <path> --image-dir <path> --output-dir <path>
    """
    logger = setup_logging()
    logger.info("Starting Grad-CAM visualization generation.")

    parser = argparse.ArgumentParser(
        description="Generate Grad-CAM visualizations for material strength prediction."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to the trained model checkpoint (.pt file).",
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        default=None,
        help="Directory containing test images. If None, uses data/processed/test/.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save visualizations. If None, uses results/grad_cam/.",
    )
    parser.add_argument(
        "--target-layer",
        type=str,
        default="features.18",
        help="Name of the target layer for Grad-CAM.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Transparency of the heatmap overlay (0.0 to 1.0).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to use (cpu, cuda). If None, auto-detect.",
    )

    args = parser.parse_args()

    # Set seed
    set_seed(args.seed)

    # Determine paths
    project_root = get_project_root()
    model_path = Path(args.model_path)
    if not model_path.is_absolute():
        model_path = project_root / args.model_path

    image_dir = (
        Path(args.image_dir)
        if args.image_dir
        else get_processed_dir() / "test"
    )
    if not image_dir.is_absolute():
        image_dir = project_root / image_dir

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else get_results_dir() / "grad_cam"
    )
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir

    device = (
        torch.device(args.device)
        if args.device
        else (
            torch.device("cuda")
            if torch.cuda.is_available()
            else torch.device("cpu")
        )
    )

    logger.info(f"Model path: {model_path}")
    logger.info(f"Image directory: {image_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Device: {device}")

    # Verify model exists
    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        sys.exit(1)

    # Verify image directory exists
    if not image_dir.exists():
        logger.error(f"Image directory not found: {image_dir}")
        sys.exit(1)

    # Load model
    logger.info("Loading model...")
    model = get_model()
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)
    model.to(device)
    model.eval()
    logger.info("Model loaded successfully.")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all images
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    image_files = [
        f for f in image_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        logger.warning(f"No images found in {image_dir}")
        sys.exit(0)

    logger.info(f"Found {len(image_files)} images to process.")

    results = []
    success_count = 0
    fail_count = 0

    for i, image_file in enumerate(image_files):
        logger.info(f"Processing [{i+1}/{len(image_files)}]: {image_file.name}")

        try:
            output_filename = f"{image_file.stem}_grad_cam.png"
            output_path = output_dir / output_filename

            result = generate_grad_cam_visualization(
                model=model,
                image_path=image_file,
                output_path=output_path,
                device=device,
                target_layer=args.target_layer,
                alpha=args.alpha,
            )
            results.append(result)
            success_count += 1
            logger.info(f"  -> Saved: {output_path}")

        except Exception as e:
            logger.error(f"  -> Failed: {e}", exc_info=True)
            fail_count += 1
            results.append({
                "original_image": str(image_file),
                "error": str(e),
                "status": "failed",
            })

    # Write summary report
    report_path = output_dir / "grad_cam_report.json"
    report = {
        "total_images": len(image_files),
        "success_count": success_count,
        "fail_count": fail_count,
        "target_layer": args.target_layer,
        "alpha": args.alpha,
        "seed": args.seed,
        "results": results,
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Summary report saved to: {report_path}")
    logger.info(
        f"Grad-CAM generation complete: {success_count} success, {fail_count} failed."
    )

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()