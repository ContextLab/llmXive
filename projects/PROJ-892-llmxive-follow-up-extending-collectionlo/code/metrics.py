import numpy as np
import torch
from PIL import Image
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import clip
import lpips
import logging

# Initialize LPIPS loss function (only once per process)
_lpips_loss = None

def _get_lpips_loss():
    global _lpips_loss
    if _lpips_loss is None:
        _lpips_loss = lpips.LPIPS(net='vgg').eval()
    return _lpips_loss

def extract_clip_image_embedding(image: Image.Image, device: str = "cpu") -> np.ndarray:
    """
    Extract CLIP image embedding for a single PIL Image.
    
    Args:
        image: PIL Image to process
        device: Device to run CLIP on (default: "cpu")
        
    Returns:
        NumPy array of image embedding
    """
    model, _ = clip.load("ViT-B/32", device=device)
    model.eval()
    
    # Preprocess image
    preprocess = clip.transforms.Compose([
        clip.transforms.Resize(224),
        clip.transforms.CenterCrop(224),
        clip.transforms.ToTensor(),
        clip.transforms.Normalize((0.48145466, 0.4578275, 0.40821073), 
                                (0.26862954, 0.26660259, 0.27656233))
    ])
    
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        embedding = model.encode_image(image_tensor)
    
    return embedding.cpu().numpy().flatten()

def extract_clip_text_embedding(text: str, device: str = "cpu") -> np.ndarray:
    """
    Extract CLIP text embedding for a single text prompt.
    
    Args:
        text: Text prompt to process
        device: Device to run CLIP on (default: "cpu")
        
    Returns:
        NumPy array of text embedding
    """
    model, _ = clip.load("ViT-B/32", device=device)
    model.eval()
    
    # Tokenize text
    tokens = clip.tokenize([text]).to(device)
    
    with torch.no_grad():
        embedding = model.encode_text(tokens)
    
    return embedding.cpu().numpy().flatten()

def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        emb1: First embedding array
        emb2: Second embedding array
        
    Returns:
        Cosine similarity score (range: -1 to 1)
    """
    emb1_norm = emb1 / np.linalg.norm(emb1)
    emb2_norm = emb2 / np.linalg.norm(emb2)
    return float(np.dot(emb1_norm, emb2_norm))

def compute_lpips_distance(image1: Image.Image, image2: Image.Image, 
                          device: str = "cpu") -> float:
    """
    Compute LPIPS (Learned Perceptual Image Patch Similarity) distance between two images.
    
    LPIPS measures perceptual similarity using a pre-trained VGG network.
    Lower values indicate higher perceptual similarity.
    
    Args:
        image1: First PIL Image
        image2: Second PIL Image
        device: Device to run LPIPS on (default: "cpu")
        
    Returns:
        LPIPS distance (float, typically 0.0-1.0)
    """
    lpips_fn = _get_lpips_loss()
    lpips_fn.to(device)
    
    # Preprocess images for LPIPS
    preprocess = lambda img: (
        torch.tensor(np.array(img).transpose(2, 0, 1)).float() / 127.5 - 1.0
    ).unsqueeze(0).to(device)
    
    img1_tensor = preprocess(image1)
    img2_tensor = preprocess(image2)
    
    with torch.no_grad():
        distance = lpips_fn(img1_tensor, img2_tensor)
    
    return float(distance.item())

def compute_image_text_similarity(image: Image.Image, text: str, 
                                 device: str = "cpu") -> float:
    """
    Compute CLIP-based similarity between an image and a text prompt.
    
    Args:
        image: PIL Image
        text: Text prompt
        device: Device to use
        
    Returns:
        Cosine similarity score
    """
    img_emb = extract_clip_image_embedding(image, device)
    txt_emb = extract_clip_text_embedding(text, device)
    return compute_cosine_similarity(img_emb, txt_emb)

def batch_compute_image_text_similarity(images: List[Image.Image], 
                                       texts: List[str], 
                                       device: str = "cpu") -> List[float]:
    """
    Compute CLIP similarity for multiple image-text pairs.
    
    Args:
        images: List of PIL Images
        texts: List of text prompts
        device: Device to use
        
    Returns:
        List of similarity scores
    """
    if len(images) != len(texts):
        raise ValueError("Number of images must match number of texts")
    
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()
    
    # Process images
    image_tensors = torch.stack([
        preprocess(image).unsqueeze(0) for image in images
    ]).to(device)
    
    with torch.no_grad():
        image_embeddings = model.encode_image(image_tensors)
    
    # Process texts
    texts_tokens = clip.tokenize(texts).to(device)
    with torch.no_grad():
        text_embeddings = model.encode_text(texts_tokens)
    
    # Compute similarities
    similarities = []
    for i in range(len(images)):
        img_norm = image_embeddings[i].cpu().numpy()
        txt_norm = text_embeddings[i].cpu().numpy()
        
        img_norm = img_norm / np.linalg.norm(img_norm)
        txt_norm = txt_norm / np.linalg.norm(txt_norm)
        
        sim = np.dot(img_norm, txt_norm)
        similarities.append(float(sim))
    
    return similarities

def compute_cesr_score(quantized_images: List[Image.Image], 
                      fp16_ref_images: List[Image.Image],
                      target_effect_idx: int,
                      device: str = "cpu") -> float:
    """
    Compute Cross-Effect Similarity Ratio (CESR) to detect concept bleeding.
    
    CESR measures how much a quantized adapter's output for a specific effect
    resembles outputs from OTHER effects (indicating concept bleeding).
    
    Args:
        quantized_images: List of images generated with quantized adapter
        fp16_ref_images: List of FP16 reference images for all effects
        target_effect_idx: Index of the target effect being tested
        device: Device to use
        
    Returns:
        CESR score (higher indicates more concept bleeding)
    """
    if len(quantized_images) != len(fp16_ref_images):
        raise ValueError("Number of quantized images must match reference images")
    
    # Get target effect image from quantized set
    target_quantized = quantized_images[target_effect_idx]
    target_fp16 = fp16_ref_images[target_effect_idx]
    
    # Compute similarity to own FP16 reference (should be high)
    own_similarity = compute_image_text_similarity(target_quantized, "target", device)
    # Use a dummy text since we're comparing image-to-image via CLIP
    # Actually, let's compute image-to-image similarity using CLIP embeddings
    target_quantized_emb = extract_clip_image_embedding(target_quantized, device)
    target_fp16_emb = extract_clip_image_embedding(target_fp16, device)
    own_similarity = compute_cosine_similarity(target_quantized_emb, target_fp16_emb)
    
    # Compute similarities to OTHER effects' FP16 references
    other_similarities = []
    for i, ref_img in enumerate(fp16_ref_images):
        if i != target_effect_idx:
            ref_emb = extract_clip_image_embedding(ref_img, device)
            sim = compute_cosine_similarity(target_quantized_emb, ref_emb)
            other_similarities.append(sim)
    
    if not other_similarities:
        return 0.0
    
    # CESR = mean similarity to other effects / similarity to own effect
    mean_other_sim = np.mean(other_similarities)
    if own_similarity == 0:
        return float('inf') if mean_other_sim > 0 else 0.0
    
    cesr = mean_other_sim / own_similarity
    return float(cesr)

def compute_lpips_matrix(image_list: List[Image.Image], 
                        device: str = "cpu") -> np.ndarray:
    """
    Compute pairwise LPIPS distance matrix for a list of images.
    
    Args:
        image_list: List of PIL Images
        device: Device to use
        
    Returns:
        NxN numpy array of LPIPS distances
    """
    n = len(image_list)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            dist = compute_lpips_distance(image_list[i], image_list[j], device)
            matrix[i, j] = dist
            matrix[j, i] = dist
    
    return matrix