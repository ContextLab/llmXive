import numpy as np
import torch
from PIL import Image
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
from transformers import CLIPProcessor, CLIPModel
import lpips

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global caches for heavy models to avoid reloading
_CLIP_MODEL = None
_CLIP_PROCESSOR = None
_LPIPS_MODEL = None

def _get_clip_models():
    """Lazy load CLIP model and processor."""
    global _CLIP_MODEL, _CLIP_PROCESSOR
    if _CLIP_MODEL is None or _CLIP_PROCESSOR is None:
        logger.info("Loading CLIP model (ViT-L/14)...")
        # Using the standard OpenCLIP model often used in these pipelines
        model_name = "openai/clip-vit-large-patch14"
        _CLIP_MODEL = CLIPModel.from_pretrained(model_name)
        _CLIP_PROCESSOR = CLIPProcessor.from_pretrained(model_name)
        
        # Move to CPU to prevent OOM on GPU-less runners, or GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _CLIP_MODEL.to(device)
        _CLIP_MODEL.eval()
    return _CLIP_MODEL, _CLIP_PROCESSOR

def _get_lpips_model():
    """Lazy load LPIPS model."""
    global _LPIPS_MODEL
    if _LPIPS_MODEL is None:
        logger.info("Loading LPIPS model...")
        # LPIPS uses a specific pretrained network (alex or vgg)
        # 'net_type': 'alex' is standard and lighter
        _LPIPS_MODEL = lpips.LPIPS(net='alex')
        _LPIPS_MODEL.eval() # Ensure eval mode
    return _LPIPS_MODEL

def extract_clip_image_embedding(image_path: Path) -> np.ndarray:
    """
    Extract CLIP image embedding for a single image.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        numpy array of shape (1, embedding_dim).
    """
    model, processor = _get_clip_models()
    device = next(model.parameters()).device
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
        
    image = Image.open(image_path).convert("RGB")
    
    inputs = processor(images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
        # Normalize the features (CLIP outputs are usually not normalized by default in all versions, 
        # but cosine similarity requires unit vectors)
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        
    return image_features.cpu().numpy().squeeze(0)

def extract_clip_text_embedding(texts: List[str]) -> np.ndarray:
    """
    Extract CLIP text embeddings for a list of texts.
    
    Args:
        texts: List of prompt strings.
        
    Returns:
        numpy array of shape (len(texts), embedding_dim).
    """
    model, processor = _get_clip_models()
    device = next(model.parameters()).device
    
    inputs = processor(text=texts, return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
        
    return text_features.cpu().numpy()

def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec_a: First vector (1D or 2D with batch dim 1).
        vec_b: Second vector (1D or 2D with batch dim 1).
        
    Returns:
        Cosine similarity score.
    """
    # Ensure 1D for simple dot product if inputs are single vectors
    if vec_a.ndim == 1:
        vec_a = vec_a.reshape(1, -1)
    if vec_b.ndim == 1:
        vec_b = vec_b.reshape(1, -1)
        
    # Dot product of normalized vectors is cosine similarity
    # vec_a and vec_b should already be normalized by the extraction functions
    similarity = np.dot(vec_a, vec_b.T)
    return float(similarity[0, 0])

def compute_image_text_similarity(image_path: Path, text: str) -> float:
    """
    Compute cosine similarity between an image and a text prompt.
    
    Args:
        image_path: Path to the image.
        text: The prompt text.
        
    Returns:
        Cosine similarity score.
    """
    img_emb = extract_clip_image_embedding(image_path)
    txt_emb = extract_clip_text_embedding([text])[0]
    return compute_cosine_similarity(img_emb, txt_emb)

def batch_compute_image_text_similarity(image_paths: List[Path], texts: List[str]) -> List[float]:
    """
    Compute similarities for a batch of images and texts.
    Assumes 1:1 mapping.
    """
    if len(image_paths) != len(texts):
        raise ValueError("Number of images must match number of texts.")
        
    results = []
    for img_path, txt in zip(image_paths, texts):
        results.append(compute_image_text_similarity(img_path, txt))
    return results

def compute_lpips_distance(img1_path: Path, img2_path: Path) -> float:
    """
    Compute LPIPS distance between two images.
    
    Args:
        img1_path: Path to first image.
        img2_path: Path to second image.
        
    Returns:
        LPIPS distance (scalar).
    """
    lpips_model = _get_lpips_model()
    device = next(lpips_model.parameters()).device
    
    def load_and_preprocess(path: Path) -> torch.Tensor:
        img = Image.open(path).convert("RGB")
        # LPIPS expects tensors in range [-1, 1]
        img_tensor = torch.from_numpy(np.array(img).astype(np.float32) / 127.5 - 1.0).permute(2, 0, 1).unsqueeze(0)
        return img_tensor.to(device)
        
    img1 = load_and_preprocess(img1_path)
    img2 = load_and_preprocess(img2_path)
    
    with torch.no_grad():
        loss = lpips_model(img1, img2, normalize=False) # normalize=False as we pre-normalized
        
    return float(loss.item())

def compute_lpips_distance_from_paths(image_paths: List[Path], reference_paths: List[Path]) -> List[float]:
    """
    Compute LPIPS distances for pairs of images.
    
    Args:
        image_paths: List of generated image paths.
        reference_paths: List of reference image paths.
        
    Returns:
        List of LPIPS distances.
    """
    if len(image_paths) != len(reference_paths):
        raise ValueError("Number of images must match number of references.")
        
    distances = []
    for img, ref in zip(image_paths, reference_paths):
        distances.append(compute_lpips_distance(img, ref))
    return distances

def compute_cesr_score(embedding: np.ndarray, reference_embeddings: np.ndarray, distractor_embeddings: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Compute Cross-Effect Similarity Ratio (CESR).
    
    Args:
        embedding: The embedding of the generated image (1, dim).
        reference_embeddings: Embeddings of 'other effect' references (N, dim).
        distractor_embeddings: Optional embeddings of distractor references (M, dim).
        
    Returns:
        Dictionary with 'cesr_raw', 'cesr_baseline', 'cesr_normalized'.
    """
    if reference_embeddings is None or reference_embeddings.size == 0:
        raise ValueError("Reference embeddings cannot be empty.")
        
    # Compute similarity to other effect references
    # cosine similarity = dot(normalized_a, normalized_b)
    # embeddings should be normalized
    sims = np.dot(reference_embeddings, embedding.T).flatten()
    cesr_raw = float(np.mean(sims))
    
    cesr_baseline = 0.0
    if distractor_embeddings is not None and distractor_embeddings.size > 0:
        distractor_sims = np.dot(distractor_embeddings, embedding.T).flatten()
        cesr_baseline = float(np.mean(distractor_sims))
        
    cesr_normalized = cesr_raw - cesr_baseline
    
    return {
        "cesr_raw": cesr_raw,
        "cesr_baseline": cesr_baseline,
        "cesr_normalized": cesr_normalized
    }

def compute_lpips_matrix(image_paths: List[Path]) -> np.ndarray:
    """
    Compute a pairwise LPIPS distance matrix for a list of images.
    
    Args:
        image_paths: List of image paths.
        
    Returns:
        Square numpy array of distances.
    """
    n = len(image_paths)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = compute_lpips_distance(image_paths[i], image_paths[j])
            matrix[i, j] = d
            matrix[j, i] = d
    return matrix