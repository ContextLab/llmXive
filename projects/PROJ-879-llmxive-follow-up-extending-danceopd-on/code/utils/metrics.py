"""
Metrics module for evaluating generative model fidelity.

Implements CPU-only CLIP Score and FID calculations.
"""
import os
import tempfile
import shutil
from typing import Union, List, Optional
from pathlib import Path
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from transformers import CLIPModel, CLIPProcessor
from torch_fidelity import calculate_metrics


class ImageDataset(torch.utils.data.Dataset):
    """Simple dataset wrapper for image paths."""
    
    def __init__(self, image_paths: List[Union[str, Path]]):
        """
        Initialize the dataset.
        
        Args:
            image_paths: List of paths to image files.
        """
        self.image_paths = [str(p) for p in image_paths]
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        try:
            image = Image.open(self.image_paths[idx]).convert('RGB')
            tensor = self.transform(image)
            return tensor
        except Exception as e:
            raise RuntimeError(f"Failed to load image {self.image_paths[idx]}: {e}")


def calculate_clip_score(
    image_path_1: Union[str, Path, List[Union[str, Path]]],
    image_path_2: Union[str, Path, List[Union[str, Path]]],
    device: str = "cpu"
) -> List[float]:
    """
    Calculate per-sample CLIP similarity scores between two sets of images.
    
    This function computes the cosine similarity between the CLIP embeddings
    of corresponding image pairs. It is designed to be CPU-only.
    
    Args:
        image_path_1: Path(s) to the first set of images (e.g., teacher baseline).
        image_path_2: Path(s) to the second set of images (e.g., student/tree generated).
        device: Device to run inference on (default: "cpu").
    
    Returns:
        List[float]: Per-sample CLIP similarity scores.
    
    Raises:
        ValueError: If the number of images in both lists does not match.
        FileNotFoundError: If any image file cannot be found.
    """
    # Normalize inputs to lists
    if isinstance(image_path_1, (str, Path)):
        image_path_1 = [image_path_1]
    if isinstance(image_path_2, (str, Path)):
        image_path_2 = [image_path_2]
    
    if len(image_path_1) != len(image_path_2):
        raise ValueError(
            f"Number of images must match. Got {len(image_path_1)} and {len(image_path_2)}."
        )
    
    if len(image_path_1) == 0:
        return []
    
    # Load CLIP model and processor
    model_name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_name).to(device)
    processor = CLIPProcessor.from_pretrained(model_name)
    model.eval()
    
    # Image transform for PIL -> Tensor (CLIP expects specific normalization)
    # We use the processor's transform logic or standard normalization
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    
    scores = []
    
    with torch.no_grad():
        for img1_path, img2_path in zip(image_path_1, image_path_2):
            # Load images
            try:
                img1 = Image.open(img1_path).convert('RGB')
                img2 = Image.open(img2_path).convert('RGB')
            except Exception as e:
                raise FileNotFoundError(f"Could not load image: {e}")
            
            # Process images
            inputs1 = processor(images=img1, return_tensors="pt", padding=True).to(device)
            inputs2 = processor(images=img2, return_tensors="pt", padding=True).to(device)
            
            # Get image embeddings
            with torch.no_grad():
                emb1 = model.get_image_features(**inputs1)
                emb2 = model.get_image_features(**inputs2)
            
            # Normalize embeddings
            emb1 = emb1 / emb1.norm(dim=-1, keepdim=True)
            emb2 = emb2 / emb2.norm(dim=-1, keepdim=True)
            
            # Calculate cosine similarity
            similarity = (emb1 * emb2).sum(dim=-1).item()
            scores.append(similarity)
    
    return scores


def calculate_fid(
    img_list_ref: List[Union[str, Path]],
    img_list_gen: List[Union[str, Path]],
    device: str = "cpu"
) -> float:
    """
    Calculate the Fréchet Inception Distance (FID) between two sets of images.
    
    This function uses the `torch-fidelity` library to compute FID on CPU.
    It expects lists of image paths.
    
    Args:
        img_list_ref: List of paths to reference images (e.g., teacher baseline).
        img_list_gen: List of paths to generated images (e.g., student/tree generated).
        device: Device to run inference on (default: "cpu"). torch-fidelity handles
                device selection internally, but we ensure CPU usage by not passing GPU args.
    
    Returns:
        float: The calculated FID score.
    
    Raises:
        ValueError: If the lists are empty.
        RuntimeError: If torch-fidelity fails to compute the metric.
    """
    if len(img_list_ref) == 0 or len(img_list_gen) == 0:
        raise ValueError("Input image lists cannot be empty.")
    
    # Create temporary directories for torch-fidelity as it expects directory inputs
    with tempfile.TemporaryDirectory() as tmp_ref, \
         tempfile.TemporaryDirectory() as tmp_gen:
        
        # Copy images to temp directories
        for i, path in enumerate(img_list_ref):
            dest = os.path.join(tmp_ref, f"ref_{i:05d}.png")
            shutil.copy2(str(path), dest)
        
        for i, path in enumerate(img_list_gen):
            dest = os.path.join(tmp_gen, f"gen_{i:05d}.png")
            shutil.copy2(str(path), dest)
        
        # Calculate FID using torch-fidelity
        # We set 'cuda' to False to force CPU usage
        metrics_dict = calculate_metrics(
            input1=tmp_ref,
            input2=tmp_gen,
            cuda=False,  # Force CPU
            verbose=False,
            quiet=True,
            fid_batch_size=32,
            feature_layer='inception_v3',
            resize=True,
            resize_height=299,
            resize_width=299,
        )
        
        fid_score = metrics_dict.get('frechet_inception_distance')
        
        if fid_score is None:
            raise RuntimeError("Failed to compute FID score. Check input image formats.")
        
        return float(fid_score)