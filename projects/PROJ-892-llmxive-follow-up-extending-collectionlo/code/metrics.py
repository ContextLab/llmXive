import numpy as np
import torch
from PIL import Image
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
import lpips
import torchvision.transforms as transforms

# Initialize LPIPS model (runs on CPU for this project context)
_lpips_vgg = None

def _get_lpips_model():
    """Lazy initialization of the LPIPS model."""
    global _lpips_vgg
    if _lpips_vgg is None:
        logging.info("Initializing LPIPS model (this may take a moment)...")
        # net_type='vgg' is the standard for perceptual similarity
        _lpips_vgg = lpips.LPIPS(net='vgg', verbose=False)
        _lpips_vgg.eval()
        _lpips_vgg.to('cpu')
    return _lpips_vgg

def extract_clip_image_embedding(image: Image.Image, device: str = 'cpu') -> torch.Tensor:
    """
    Extract CLIP image embedding.
    Requires 'clip' package to be installed.
    """
    try:
        import clip
    except ImportError:
        raise ImportError("The 'clip' package is required for this function. Install it via 'pip install git+https://github.com/openai/CLIP.git'")

    model, _ = clip.load("ViT-B/32", device=device, download_root=str(Path.home() / ".cache/clip"))
    model.eval()

    preprocess = transforms.Compose([
        transforms.Resize(224),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)),
    ])

    image_tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model.encode_image(image_tensor)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding

def extract_clip_text_embedding(text: str, device: str = 'cpu') -> torch.Tensor:
    """
    Extract CLIP text embedding.
    """
    try:
        import clip
    except ImportError:
        raise ImportError("The 'clip' package is required for this function.")

    model, _ = clip.load("ViT-B/32", device=device, download_root=str(Path.home() / ".cache/clip"))
    model.eval()

    tokens = clip.tokenize([text]).to(device)
    with torch.no_grad():
        embedding = model.encode_text(tokens)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding

def compute_cosine_similarity(embedding1: torch.Tensor, embedding2: torch.Tensor) -> float:
    """Compute cosine similarity between two embeddings."""
    if embedding1.dim() == 1:
        embedding1 = embedding1.unsqueeze(0)
    if embedding2.dim() == 1:
        embedding2 = embedding2.unsqueeze(0)
    
    sim = torch.nn.functional.cosine_similarity(embedding1, embedding2)
    return sim.item()

def compute_lpips_distance(image1: Image.Image, image2: Image.Image, device: str = 'cpu') -> float:
    """
    Compute LPIPS distance between two PIL Images.
    
    Args:
        image1: First PIL Image.
        image2: Second PIL Image.
        device: Device to run the model on (default 'cpu').
        
    Returns:
        float: The LPIPS distance (lower is more similar).
        
    Note:
        This function assumes images are RGB. If grayscale, it will be converted.
        The function uses the pre-trained VGG network from the lpips library.
    """
    lpips_model = _get_lpips_model()
    
    # Ensure images are RGB
    if image1.mode != 'RGB':
        image1 = image1.convert('RGB')
    if image2.mode != 'RGB':
        image2 = image2.convert('RGB')
        
    # Transform to tensors and normalize to [-1, 1] as required by LPIPS
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    img1_tensor = transform(image1).unsqueeze(0).to(device)
    img2_tensor = transform(image2).unsqueeze(0).to(device)
    
    with torch.no_grad():
        # LPIPS returns a distance tensor
        distance = lpips_model(img1_tensor, img2_tensor, normalize=True)
        
    return float(distance.item())

def compute_image_text_similarity(image: Image.Image, text: str, device: str = 'cpu') -> float:
    """Compute cosine similarity between an image and text using CLIP."""
    img_emb = extract_clip_image_embedding(image, device)
    txt_emb = extract_clip_text_embedding(text, device)
    return compute_cosine_similarity(img_emb, txt_emb)

def batch_compute_image_text_similarity(images: List[Image.Image], texts: List[str], device: str = 'cpu') -> List[float]:
    """Compute similarity for a batch of image-text pairs."""
    results = []
    for img, txt in zip(images, texts):
        results.append(compute_image_text_similarity(img, txt, device))
    return results

def compute_cesr_score(quantized_images: List[Image.Image], 
                       target_prompt: str, 
                       reference_images: Dict[str, List[Image.Image]], 
                       device: str = 'cpu') -> float:
    """
    Compute Cross-Effect Similarity Ratio (CESR).
    
    Compares quantized output embeddings against the FP16 ReferenceImages 
    for *other* effect prompts (excluding the target prompt) to detect concept bleeding.
    
    Args:
        quantized_images: List of generated images for the target prompt using quantized adapter.
        target_prompt: The prompt used to generate the quantized_images.
        reference_images: Dict mapping effect prompt -> list of FP16 reference images for that prompt.
        device: Device for computation.
        
    Returns:
        float: The mean CESR score. Lower indicates less bleeding (better separation).
    """
    if not quantized_images:
        raise ValueError("quantized_images list is empty.")
        
    # Get embeddings for the quantized images (target)
    target_embeddings = []
    for img in quantized_images:
        emb = extract_clip_image_embedding(img, device)
        target_embeddings.append(emb)
    target_emb_avg = torch.mean(torch.stack(target_embeddings), dim=0)
    
    # Collect reference embeddings for NON-target prompts
    other_prompts = [p for p in reference_images.keys() if p != target_prompt]
    if not other_prompts:
        logging.warning(f"No other prompts found in reference_images to compute CESR for target '{target_prompt}'.")
        return 0.0
        
    other_embeddings = []
    for prompt, imgs in reference_images.items():
        for img in imgs:
            emb = extract_clip_image_embedding(img, device)
            other_embeddings.append(emb)
            
    if not other_embeddings:
        return 0.0
        
    other_emb_avg = torch.mean(torch.stack(other_embeddings), dim=0)
    
    # Compute similarity between target average and other average
    # CESR typically measures how much the target looks like "others".
    # High similarity = High bleeding.
    similarity = compute_cosine_similarity(target_emb_avg.unsqueeze(0), other_emb_avg.unsqueeze(0))
    
    return float(similarity)

def compute_lpips_matrix(image_list: List[Image.Image], device: str = 'cpu') -> np.ndarray:
    """
    Compute a pairwise LPIPS distance matrix for a list of images.
    
    Args:
        image_list: List of PIL Images.
        device: Device for computation.
        
    Returns:
        np.ndarray: Square matrix of shape (N, N) where N is len(image_list).
    """
    n = len(image_list)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            dist = compute_lpips_distance(image_list[i], image_list[j], device)
            matrix[i, j] = dist
            matrix[j, i] = dist
            
    return matrix