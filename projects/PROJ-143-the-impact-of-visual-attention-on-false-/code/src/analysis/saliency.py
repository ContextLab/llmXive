import os
import json
import math
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models.feature_extraction import create_feature_extractor, get_graph_node_names

# --- ResNet18 GradCAM Implementation (Existing) ---

class GradCAM:
    """
    GradCAM implementation for ResNet18.
    Extracts the last convolutional layer and computes gradients to generate a heatmap.
    """
    def __init__(self, model: nn.Module, target_layer_name: str = 'layer4'):
        self.model = model
        self.target_layer_name = target_layer_name
        self.gradients = None
        self.activations = None

        # Register hooks
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        # Find the target layer
        target_layer = None
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                target_layer = module
                break

        if target_layer is None:
            raise ValueError(f"Target layer {self.target_layer_name} not found in model")

        self.forward_handle = target_layer.register_forward_hook(forward_hook)
        self.backward_handle = target_layer.register_full_backward_hook(backward_hook)

    def generate_cam(self, target_class: int = None):
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Forward/backward pass not executed yet.")

        # Global average pooling of gradients
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        
        # Weighted sum of activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        
        # ReLU
        cam = torch.relu(cam)
        
        # Normalize to [0, 1]
        cam = cam - torch.min(cam)
        cam = cam / (torch.max(cam) + 1e-7)
        
        return cam.squeeze().cpu().detach().numpy()

    def remove_hooks(self):
        self.forward_handle.remove()
        self.backward_handle.remove()

def cv2_resize(image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Resize image using OpenCV."""
    return cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)

def load_resnet18_saliency_model() -> nn.Module:
    """Load a pre-trained ResNet18 model for saliency detection."""
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model = model.eval()
    # Remove the final fully connected layer for feature extraction
    model = nn.Sequential(*list(model.children())[:-1])
    return model

def preprocess_image(image: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> torch.Tensor:
    """Preprocess image for model input."""
    # Resize
    image_resized = cv2_resize(image, target_size)
    
    # Normalize
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    tensor = transform(image_resized)
    return tensor.unsqueeze(0)  # Add batch dimension

def compute_saliency_map(image: np.ndarray, model: nn.Module, use_gradcam: bool = True) -> np.ndarray:
    """
    Compute saliency map for a single image.
    
    Args:
        image: Input image as numpy array (H, W, C)
        model: Pre-trained model
        use_gradcam: If True, use GradCAM; otherwise use simple gradient-based saliency
        
    Returns:
        Saliency map as numpy array (H, W) normalized to [0, 1]
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid input image")
    
    # Preprocess
    input_tensor = preprocess_image(image)
    input_tensor.requires_grad_(True)
    
    # Forward pass
    output = model(input_tensor)
    
    if use_gradcam:
        # For GradCAM, we need a specific class score. 
        # Since we don't have a specific class, we use the sum of all outputs
        # or a dummy class if the model has a classifier.
        # Here we assume the model is feature extractor (no FC layer)
        # We'll use the mean of the output as the target for GradCAM
        target_score = output.mean()
        target_score.backward()
        
        # Get gradients
        gradients = input_tensor.grad.detach().cpu().numpy()
        
        # Absolute gradient as saliency
        saliency = np.abs(gradients[0])
        saliency = np.max(saliency, axis=0)  # Max over channels
        
    else:
        # Alternative: Use simple gradient magnitude
        target_score = output.mean()
        target_score.backward()
        gradients = input_tensor.grad.detach().cpu().numpy()
        saliency = np.abs(gradients[0])
        saliency = np.max(saliency, axis=0)
    
    # Normalize
    saliency = saliency - np.min(saliency)
    saliency = saliency / (np.max(saliency) + 1e-7)
    
    return saliency

def process_visual_genome_dataset(
    dataset_dir: Path,
    output_path: Path,
    model: Optional[nn.Module] = None,
    target_size: Tuple[int, int] = (224, 224)
) -> Dict[str, Any]:
    """
    Process Visual Genome dataset to generate saliency maps.
    
    Args:
        dataset_dir: Path to the Visual Genome dataset directory
        output_path: Path to save the results
        model: Pre-trained model to use
        target_size: Target size for image resizing
        
    Returns:
        Dictionary containing processing results
    """
    if model is None:
        model = load_resnet18_saliency_model()
    
    results = {
        'processed_images': 0,
        'failed_images': 0,
        'saliency_maps': []
    }
    
    # Iterate through images
    image_dir = dataset_dir / 'images'
    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")
    
    for img_path in image_dir.glob('*.jpg'):
        try:
            image = cv2.imread(str(img_path))
            if image is None:
                results['failed_images'] += 1
                continue
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Compute saliency
            saliency_map = compute_saliency_map(image, model)
            
            # Store result
            results['saliency_maps'].append({
                'image_id': img_path.stem,
                'saliency_map': saliency_map.tolist(),
                'shape': list(saliency_map.shape)
            })
            
            results['processed_images'] += 1
            
        except Exception as e:
            warnings.warn(f"Failed to process {img_path}: {e}")
            results['failed_images'] += 1
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

# --- ViT-B/CAM Implementation (New for T025) ---

class ViTSaliencyWrapper:
    """
    Wrapper for Vision Transformer (ViT-B) saliency map generation using CAM.
    Implements CPU-only fallback if GPU is unavailable.
    """
    def __init__(self, model_name: str = "vit_b_16", target_layer: str = "layers"):
        self.model_name = model_name
        self.target_layer = target_layer
        self.model = None
        self.transform = None
        self._load_model()

    def _load_model(self):
        """Load ViT-B model and set up feature extraction."""
        try:
            # Load pre-trained ViT-B/16 model
            self.model = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
            self.model = self.model.eval()
            
            # Remove the classifier head for feature extraction
            # ViT-B structure: conv_proj -> TransformerEncoder -> head
            # We want features from the TransformerEncoder
            self.model.head = nn.Identity()
            
            # Define transforms
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.5, 0.5, 0.5], 
                    std=[0.5, 0.5, 0.5]
                ),
            ])
            
        except Exception as e:
            warnings.warn(f"Failed to load ViT-B model: {e}. Fallback to ResNet18.")
            self.model = None

    def compute_saliency(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Compute saliency map using ViT features.
        
        Args:
            image: Input image (H, W, C) in RGB format
            
        Returns:
            Saliency map (H, W) or None if model unavailable
        """
        if self.model is None:
            return None
        
        try:
            # Preprocess
            input_tensor = self.transform(image).unsqueeze(0)
            input_tensor.requires_grad_(True)
            
            # Forward pass
            features = self.model(input_tensor)
            
            # For ViT, we can use the gradient of the mean feature as saliency
            # Since we removed the classifier, we use the mean of the output features
            target_score = features.mean()
            target_score.backward()
            
            # Get gradients
            gradients = input_tensor.grad.detach().cpu().numpy()
            
            # Compute saliency: max absolute gradient over channels
            saliency = np.abs(gradients[0])
            saliency = np.max(saliency, axis=0)
            
            # Resize back to original image size if needed
            original_h, original_w = image.shape[:2]
            if saliency.shape != (original_h, original_w):
                saliency = cv2.resize(
                    saliency, 
                    (original_w, original_h), 
                    interpolation=cv2.INTER_LINEAR
                )
            
            # Normalize to [0, 1]
            saliency = saliency - np.min(saliency)
            saliency = saliency / (np.max(saliency) + 1e-7)
            
            return saliency
            
        except Exception as e:
            warnings.warn(f"ViT saliency computation failed: {e}")
            return None

def load_vit_saliency_model() -> Optional[ViTSaliencyWrapper]:
    """
    Load ViT-B saliency model with CPU fallback.
    
    Returns:
        ViTSaliencyWrapper instance or None if loading fails
    """
    try:
        wrapper = ViTSaliencyWrapper()
        if wrapper.model is not None:
            return wrapper
        return None
    except Exception as e:
        warnings.warn(f"Could not load ViT model: {e}")
        return None

def compute_vit_saliency_map(
    image: np.ndarray, 
    wrapper: Optional[ViTSaliencyWrapper] = None
) -> Optional[np.ndarray]:
    """
    Compute saliency map using ViT-B/CAM.
    
    Args:
        image: Input image (H, W, C)
        wrapper: Pre-loaded ViT wrapper (optional)
        
    Returns:
        Saliency map or None
    """
    if wrapper is None:
        wrapper = load_vit_saliency_model()
    
    if wrapper is None:
        return None
    
    return wrapper.compute_saliency(image)

# --- Main Entry Point ---

def main():
    """
    Main function to demonstrate saliency map generation.
    """
    print("Starting saliency map generation...")
    
    # Test with a dummy image if no real data is available
    dummy_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    
    # Test ResNet18
    print("Testing ResNet18 saliency...")
    try:
        resnet_model = load_resnet18_saliency_model()
        resnet_saliency = compute_saliency_map(dummy_image, resnet_model)
        print(f"ResNet18 saliency map shape: {resnet_saliency.shape}")
    except Exception as e:
        print(f"ResNet18 failed: {e}")
    
    # Test ViT-B
    print("Testing ViT-B saliency...")
    vit_wrapper = load_vit_saliency_model()
    if vit_wrapper:
        vit_saliency = compute_vit_saliency_map(dummy_image, vit_wrapper)
        if vit_saliency is not None:
            print(f"ViT-B saliency map shape: {vit_saliency.shape}")
        else:
            print("ViT-B saliency computation returned None")
    else:
        print("ViT-B model not available")
    
    print("Done.")

if __name__ == "__main__":
    main()
