import numpy as np
import torch
from PIL import Image
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
import lpips
from torchvision import transforms

# Initialize LPIPS model once at module level to avoid repeated loading overhead
_lpips_model = None
_lpips_device = None

def _get_lpips_model(device: str = "cpu"):
    """
    Lazy initialization of the LPIPS model.
    Uses 'alex' network which is standard for LPIPS.
    """
    global _lpips_model, _lpips_device
    if _lpips_model is None or _lpips_device != device:
        logging.info(f"Initializing LPIPS model on {device}...")
        # lpips.LPIPS handles download of pretrained weights on first call
        _lpips_model = lpips.LPIPS(net='alex').to(device)
        _lpips_model.eval()
        _lpips_device = device
        logging.info("LPIPS model initialized.")
    return _lpips_model

def extract_clip_image_embedding(image: Image.Image, clip_model, clip_preprocess) -> torch.Tensor:
    """
    Extract CLIP image embedding.
    """
    input_image = clip_preprocess(image).unsqueeze(0).to(clip_model.device)
    with torch.no_grad():
        embedding = clip_model.encode_image(input_image)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding

def extract_clip_text_embedding(text: str, clip_model, clip_preprocess) -> torch.Tensor:
    """
    Extract CLIP text embedding.
    """
    input_text = clip_preprocess(text).to(clip_model.device)
    with torch.no_grad():
        embedding = clip_model.encode_text(input_text)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding

def compute_cosine_similarity(emb1: torch.Tensor, emb2: torch.Tensor) -> float:
    """
    Compute cosine similarity between two embeddings.
    """
    if emb1.dim() == 1 and emb2.dim() == 1:
        return float(torch.dot(emb1, emb2).item())
    elif emb1.dim() == 2 and emb2.dim() == 2:
        # Batch similarity (dot product of normalized vectors)
        return float(torch.dot(emb1.flatten(), emb2.flatten()).item())
    else:
        raise ValueError("Embeddings must be 1D or 2D tensors.")

def compute_image_text_similarity(image: Image.Image, text: str, clip_model, clip_preprocess) -> float:
    """
    Compute similarity between an image and a text prompt.
    """
    img_emb = extract_clip_image_embedding(image, clip_model, clip_preprocess)
    txt_emb = extract_clip_text_embedding(text, clip_model, clip_preprocess)
    return compute_cosine_similarity(img_emb, txt_emb)

def batch_compute_image_text_similarity(images: List[Image.Image], texts: List[str], clip_model, clip_preprocess) -> List[float]:
    """
    Compute similarity for a batch of images and texts.
    """
    if len(images) != len(texts):
        raise ValueError("Images and texts lists must be of equal length.")
    
    similarities = []
    for img, txt in zip(images, texts):
        sim = compute_image_text_similarity(img, txt, clip_model, clip_preprocess)
        similarities.append(sim)
    return similarities

def compute_lpips_distance(image1: Image.Image, image2: Image.Image, device: str = "cpu") -> float:
    """
    Compute LPIPS distance between two PIL Images.
    
    FR-005: Computes the Learned Perceptual Image Patch Similarity (LPIPS)
    distance between a generated FP16 image and its corresponding ReferenceImage.
    
    Args:
        image1: The first image (e.g., generated baseline).
        image2: The second image (e.g., reference).
        device: Device to run the LPIPS model on (default: "cpu" for safety).
    
    Returns:
        A float representing the LPIPS distance (0 = identical, higher = more different).
    
    Raises:
        RuntimeError: If images cannot be converted to tensors properly.
    """
    if image1.mode != 'RGB':
        image1 = image1.convert('RGB')
    if image2.mode != 'RGB':
        image2 = image2.convert('RGB')

    # Ensure images are resized to a common resolution if necessary (LPIPS expects specific sizes usually, 
    # but the model handles resizing internally or we can standardize to 256x256 or similar).
    # Standard practice for LPIPS is to resize to 256x256 if not already, though the model is robust.
    # We will resize to 256x256 to ensure consistency with typical evaluation pipelines.
    target_size = (256, 256)
    image1 = image1.resize(target_size, Image.LANCZOS)
    image2 = image2.resize(target_size, Image.LANCZOS)

    lpips_model = _get_lpips_model(device)

    # Define transform: normalize to [-1, 1]
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])

    try:
        img1_tensor = transform(image1).unsqueeze(0).to(device)
        img2_tensor = transform(image2).unsqueeze(0).to(device)
        
        with torch.no_grad():
            # lpips_model returns a tensor of shape (1, 1, H, W) or (1, 1) depending on version
            # We take the mean to get a single scalar score per image pair
            score = lpips_model(img1_tensor, img2_tensor)
            return float(score.mean().item())
    except Exception as e:
        logging.error(f"Error computing LPIPS distance: {e}")
        raise

def compute_cesr_score(target_embedding: torch.Tensor, reference_embeddings: List[torch.Tensor]) -> float:
    """
    Compute Cross-Effect Similarity Ratio (CESR).
    
    FR-011: Measures how much a generated image (target) resembles *other* effects
    compared to its own effect (handled by excluding self in the caller).
    
    Args:
        target_embedding: The embedding of the target generated image.
        reference_embeddings: List of embeddings from other effect references.
    
    Returns:
        The average cosine similarity between target and the reference set.
    """
    if not reference_embeddings:
        return 0.0
    
    similarities = []
    for ref_emb in reference_embeddings:
        sim = compute_cosine_similarity(target_embedding, ref_emb)
        similarities.append(sim)
    
    return float(np.mean(similarities))

def compute_lpips_matrix(image_paths: List[Path], device: str = "cpu") -> np.ndarray:
    """
    Compute a pairwise LPIPS distance matrix for a list of image paths.
    
    Args:
        image_paths: List of paths to images.
        device: Device for computation.
    
    Returns:
        A square numpy array where [i, j] is the LPIPS distance between image i and j.
    """
    n = len(image_paths)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        img_i = Image.open(image_paths[i])
        for j in range(i + 1, n):
            img_j = Image.open(image_paths[j])
            dist = compute_lpips_distance(img_i, img_j, device)
            matrix[i, j] = dist
            matrix[j, i] = dist
    
    return matrix

def compute_lpips_distance_from_paths(path1: str, path2: str, device: str = "cpu") -> float:
    """
    Compute LPIPS distance directly from file paths.
    
    Args:
        path1: Path to first image.
        path2: Path to second image.
        device: Device for computation.
    
    Returns:
        LPIPS distance as a float.
    """
    img1 = Image.open(path1)
    img2 = Image.open(path2)
    return compute_lpips_distance(img1, img2, device)

def compute_lpips_batch(generated_images: List[Image.Image], reference_images: List[Image.Image], device: str = "cpu") -> List[float]:
    """
    Compute LPIPS distances for a batch of generated vs reference images.
    
    Args:
        generated_images: List of generated images.
        reference_images: List of corresponding reference images.
        device: Device for computation.
    
    Returns:
        List of LPIPS distances.
    """
    if len(generated_images) != len(reference_images):
        raise ValueError("Generated and reference image lists must be of equal length.")
    
    distances = []
    for gen, ref in zip(generated_images, reference_images):
        dist = compute_lpips_distance(gen, ref, device)
        distances.append(dist)
    
    return distances

def compute_lpips_distance_for_task(generated_image_path: str, reference_image_path: str, device: str = "cpu") -> float:
    """
    Specific wrapper for T013 to compute LPIPS between a generated FP16 image
    and its FP16 ReferenceImage.
    
    Args:
        generated_image_path: Path to the generated image (from T011).
        reference_image_path: Path to the reference image (from T011c).
        device: Device for computation.
    
    Returns:
        LPIPS distance.
    """
    logging.info(f"Computing LPIPS distance between:\n  Generated: {generated_image_path}\n  Reference: {reference_image_path}")
    return compute_lpips_distance_from_paths(generated_image_path, reference_image_path, device)