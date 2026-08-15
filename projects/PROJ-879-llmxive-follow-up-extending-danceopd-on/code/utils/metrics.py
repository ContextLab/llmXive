"""
Metrics module for calculating image similarity and quality metrics.

This module provides functions to compute CLIP Score and Fréchet Inception Distance (FID)
between images or directories of images. These metrics are used to evaluate the fidelity
of generated images against ground truth or baseline images.

Dependencies:
    - transformers: For CLIP model and processor
    - torch-fidelity: For FID calculation
    - torch, torchvision, PIL: For image loading and transformation
"""

import os
import tempfile
import shutil
from typing import Union, List, Optional
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
    TORCH_FIDELITY_AVAILABLE: bool = True
except ImportError:
    TORCH_FIDELITY_AVAILABLE: bool = False


class ImageDataset(Dataset):
    """
    Simple dataset class to load images for FID calculation.

    This dataset loads images from a list of file paths and applies optional
    transformations. It is specifically designed to work with the torch-fidelity
    library for computing FID scores.

    Attributes:
        image_paths (List[str]): List of paths to image files.
        transform (Optional[transforms.Compose]): Optional transformation pipeline.
    """

    def __init__(
        self,
        image_paths: List[Union[str, Path]],
        transform: Optional[transforms.Compose] = None
    ) -> None:
        """
        Initialize the ImageDataset.

        Args:
            image_paths: List of paths to image files.
            transform: Optional transformation pipeline. Defaults to a resize to 299x299
                       and conversion to tensor if not provided.
        """
        self.image_paths: List[str] = [str(p) for p in image_paths]
        self.transform: transforms.Compose = transform or transforms.Compose([
            transforms.Resize((299, 299)),
            transforms.ToTensor()
        ])

    def __len__(self) -> int:
        """
        Return the number of images in the dataset.

        Returns:
            int: Total number of images.
        """
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> torch.Tensor:
        """
        Load and transform an image at the given index.

        Args:
            idx (int): Index of the image to retrieve.

        Returns:
            torch.Tensor: Transformed image tensor.

        Raises:
            IndexError: If the index is out of range.
        """
        img_path: str = self.image_paths[idx]
        img: Image.Image = Image.open(img_path).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img


def calculate_clip_score(
    image_path_1: Union[str, Path],
    image_path_2: Union[str, Path]
) -> float:
    """
    Calculate CLIP Score between two images.

    The CLIP Score measures the cosine similarity between the image embeddings
    of two images using a pre-trained CLIP model. Higher scores indicate greater
    similarity.

    Args:
        image_path_1: Path to the first image.
        image_path_2: Path to the second image.

    Returns:
        float: CLIP similarity score between 0 and 1 (after cosine similarity).

    Raises:
        ImportError: If the 'transformers' library is not installed.
        FileNotFoundError: If either image path does not exist.
        RuntimeError: If the CLIP model fails to load or process images.

    Example:
        >>> score = calculate_clip_score("img1.png", "img2.png")
        >>> print(f"Similarity: {score:.4f}")
    """
    try:
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as e:
        raise ImportError(
            "transformers library is required for CLIP score calculation. "
            "Please install it: pip install transformers"
        ) from e

    # Load model and processor
    model_name: str = "openai/clip-vit-base-patch32"
    model: CLIPModel = CLIPModel.from_pretrained(model_name)
    processor: CLIPProcessor = CLIPProcessor.from_pretrained(model_name)

    # Load images
    img1: Image.Image = Image.open(image_path_1).convert('RGB')
    img2: Image.Image = Image.open(image_path_2).convert('RGB')

    # Process images
    inputs = processor(images=[img1, img2], return_tensors="pt", padding=True)

    # Get features
    with torch.no_grad():
        image_features: torch.Tensor = model.get_image_features(**inputs)

    # Normalize features
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    # Calculate cosine similarity
    similarity: torch.Tensor = torch.cosine_similarity(
        image_features[0:1],
        image_features[1:2]
    )

    return float(similarity.item())


def calculate_fid(
    image_path_1: Union[str, Path],
    image_path_2: Union[str, Path]
) -> float:
    """
    Calculate FID (Fréchet Inception Distance) between two images or directories.

    This function handles both single image comparisons (by creating temporary
    directories) and directory-to-directory comparisons. FID measures the
    similarity between two sets of images based on features extracted from
    an Inception-v3 network.

    Args:
        image_path_1: Path to the first image or directory of images.
        image_path_2: Path to the second image or directory of images.

    Returns:
        float: FID score. Lower values indicate more similar distributions.

    Raises:
        ImportError: If 'torch-fidelity' is not installed.
        FileNotFoundError: If input paths do not exist.
        RuntimeError: If FID calculation fails.

    Note:
        - If single images are provided, temporary directories are created.
        - The function uses Inception-v3 features (standard for FID).
        - CUDA is used if available, otherwise CPU inference is performed.
    """
    if not TORCH_FIDELITY_AVAILABLE:
        raise ImportError(
            "torch-fidelity is required for FID calculation. "
            "Please install it: pip install torch-fidelity"
        )

    path1: Path = Path(image_path_1)
    path2: Path = Path(image_path_2)

    # If inputs are single files, create temporary directories
    temp_dir1: Optional[str] = None
    temp_dir2: Optional[str] = None

    try:
        if path1.is_file():
            temp_dir1 = tempfile.mkdtemp()
            temp_path1 = Path(temp_dir1) / "img1.png"
            shutil.copy(path1, temp_path1)
            input1: str = str(temp_dir1)
        else:
            input1 = str(path1)

        if path2.is_file():
            temp_dir2 = tempfile.mkdtemp()
            temp_path2 = Path(temp_dir2) / "img2.png"
            shutil.copy(path2, temp_path2)
            input2: str = str(temp_dir2)
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
            shutil.rmtree(temp_dir1)
        if temp_dir2 and os.path.exists(temp_dir2):
            shutil.rmtree(temp_dir2)
