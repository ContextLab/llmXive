import os
import tempfile
from typing import Union, List
from pathlib import Path
import torch
import numpy as np
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import DataLoader, Dataset

# Attempt to import torch-fidelity for FID calculation
# This is a heavy dependency, so we handle import errors gracefully but fail loudly if needed
try:
    import torch_fidelity
    TORCH_FIDELITY_AVAILABLE = True
except ImportError:
    TORCH_FIDELITY_AVAILABLE = False


class ImageDataset(Dataset):
    """Simple dataset to load images for FID calculation."""
    def __init__(self, image_paths: List[Union[str, Path]], transform=None):
        self.image_paths = [str(p) for p in image_paths]
        self.transform = transform or transforms.Compose([
            transforms.Resize((299, 299)),
            transforms.ToTensor()
        ])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img


def calculate_clip_score(image_path_1: Union[str, Path], image_path_2: Union[str, Path]) -> float:
    """
    Calculate CLIP Score between two images.
    
    Args:
        image_path_1: Path to first image
        image_path_2: Path to second image
        
    Returns:
        CLIP similarity score (float)
    """
    try:
        from transformers import CLIPModel, CLIPProcessor
    except ImportError:
        raise ImportError(
            "transformers library is required for CLIP score calculation. "
            "Please install it: pip install transformers"
        )

    # Load model and processor
    model_name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)

    # Load images
    img1 = Image.open(image_path_1).convert('RGB')
    img2 = Image.open(image_path_2).convert('RGB')

    # Process images
    inputs = processor(images=[img1, img2], return_tensors="pt", padding=True)

    # Get features
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)

    # Normalize features
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    # Calculate cosine similarity
    similarity = torch.cosine_similarity(image_features[0:1], image_features[1:2])

    return float(similarity.item())


def calculate_fid(image_path_1: Union[str, Path], image_path_2: Union[str, Path]) -> float:
    """
    Calculate FID (Fréchet Inception Distance) between two images or directories.
    
    This function handles both single image comparisons (by creating temporary directories)
    and directory-to-directory comparisons.
    
    Args:
        image_path_1: Path to first image or directory of images
        image_path_2: Path to second image or directory of images
        
    Returns:
        FID score (float)
    """
    if not TORCH_FIDELITY_AVAILABLE:
        raise ImportError(
            "torch-fidelity is required for FID calculation. "
            "Please install it: pip install torch-fidelity"
        )

    path1 = Path(image_path_1)
    path2 = Path(image_path_2)

    # If inputs are single files, create temporary directories
    temp_dir1 = None
    temp_dir2 = None

    try:
        if path1.is_file():
            temp_dir1 = tempfile.mkdtemp()
            temp_path1 = Path(temp_dir1) / "img1.png"
            import shutil
            shutil.copy(path1, temp_path1)
            input1 = str(temp_dir1)
        else:
            input1 = str(path1)

        if path2.is_file():
            temp_dir2 = tempfile.mkdtemp()
            temp_path2 = Path(temp_dir2) / "img2.png"
            import shutil
            shutil.copy(path2, temp_path2)
            input2 = str(temp_dir2)
        else:
            input2 = str(path2)

        # Calculate FID using torch-fidelity
        # We use inception-v3 features which is standard for FID
        metrics = torch_fidelity.calculate_metrics(
            input1=input1,
            input2=input2,
            cuda=True if torch.cuda.is_available() else False,
            fid=True,
            verbose=False
        )

        return float(metrics['frechet_inception_distance'])

    finally:
        # Clean up temporary directories
        if temp_dir1 and os.path.exists(temp_dir1):
            import shutil
            shutil.rmtree(temp_dir1)
        if temp_dir2 and os.path.exists(temp_dir2):
            import shutil
            shutil.rmtree(temp_dir2)