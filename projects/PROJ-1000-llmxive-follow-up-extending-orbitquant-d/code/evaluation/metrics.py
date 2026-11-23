import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import json
from PIL import Image
import io

# Lazy imports for heavy dependencies to avoid startup errors if not needed
_clip = None
_fid = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _ensure_clip():
    global _clip
    if _clip is None:
        try:
            import clip
            _clip = clip
            # Load the standard model on CPU as per task requirement
            model, _ = clip.load("ViT-B/32", device="cpu")
            _clip.model = model
            logger.info("CLIP model loaded on CPU.")
        except ImportError:
            raise RuntimeError(
                "clip package not found. Install with: pip install git+https://github.com/openai/CLIP.git"
            )

def _ensure_fid():
    global _fid
    if _fid is None:
        try:
            from pytorch_fid import fid_score
            _fid = fid_score
            logger.info("FID module loaded.")
        except ImportError:
            raise RuntimeError(
                "pytorch-fid package not found. Install with: pip install pytorch-fid"
            )

def compute_mse(tensor1: torch.Tensor, tensor2: torch.Tensor) -> float:
    """
    Computes Mean Squared Error between two tensors.
    """
    if tensor1.shape != tensor2.shape:
        raise ValueError(f"Tensor shapes mismatch: {tensor1.shape} vs {tensor2.shape}")
    if tensor1.device != tensor2.device:
        tensor2 = tensor2.to(tensor1.device)
    
    mse_val = torch.mean((tensor1 - tensor2) ** 2)
    return float(mse_val.item())

def compute_clip_score(images: List[torch.Tensor], prompts: List[str]) -> float:
    """
    Computes the average CLIP score (image-text similarity) for a batch.
    Uses CLIP ViT-B/32 on CPU.
    
    Args:
        images: List of PIL Images or torch tensors (C, H, W) in range [0, 1].
        prompts: List of text prompts.
    
    Returns:
        Average CLIP similarity score (float).
    """
    if not images or not prompts:
        return 0.0
    
    clip_module = _ensure_clip()
    model, preprocess = clip_module.load("ViT-B/32", device="cpu")
    model.eval()

    # Process images
    image_inputs = []
    for img in images:
        if isinstance(img, torch.Tensor):
            # If tensor is [C, H, W], ensure it's normalized correctly for CLIP
            # CLIP expects float32, normalized to mean=[0.48145466, 0.4578275, 0.40821073], std=[0.26862954, 0.26663742, 0.2762149]
            # Assuming input is [0, 1] range.
            if img.max() > 1.0:
                img = img / 255.0
            if img.dtype != torch.float32:
                img = img.float()
            # Normalize
            mean = torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(3, 1, 1)
            std = torch.tensor([0.26862954, 0.26663742, 0.2762149]).view(3, 1, 1)
            img = (img - mean) / std
            image_inputs.append(img)
        elif isinstance(img, Image.Image):
            image_inputs.append(preprocess(img))
        else:
            raise TypeError(f"Unsupported image type: {type(img)}")
    
    image_tensor = torch.stack(image_inputs).to("cpu")

    # Process text
    text_inputs = clip_module.tokenize(prompts).to("cpu")

    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        text_features = model.encode_text(text_inputs)
        
        # Normalize features
        image_features = image_features / image_features.norm(dim=1, keepdim=True)
        text_features = text_features / text_features.norm(dim=1, keepdim=True)
        
        # Calculate cosine similarity
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=1)
        
        # Diagonal elements represent the match between image i and prompt i
        scores = similarity.diag()
        
    return float(scores.mean().item())

def compute_fid(real_images_dir: str, generated_images_dir: str) -> float:
    """
    Computes Fréchet Inception Distance (FID) between two directories of images.
    Uses pytorch-fid on CPU.
    
    Args:
        real_images_dir: Path to directory containing real images.
        generated_images_dir: Path to directory containing generated images.
    
    Returns:
        FID score (float).
    """
    fid_module = _ensure_fid()
    
    # Convert paths to Path objects if strings
    path1 = Path(real_images_dir)
    path2 = Path(generated_images_dir)
    
    if not path1.exists():
        raise FileNotFoundError(f"Real images directory not found: {path1}")
    if not path2.exists():
        raise FileNotFoundError(f"Generated images directory not found: {path2}")
    
    # pytorch_fid.fid_score expects paths to be strings and calculates internally
    # We need to pass the arguments as a list of paths
    try:
        fid_value = fid_module.calculate_fid_given_paths(
            [str(path1), str(path2)],
            batch_size=50,
            device="cpu",
            dims=2048,
            num_workers=0
        )
        return float(fid_value)
    except Exception as e:
        logger.error(f"FID calculation failed: {e}")
        raise

def compute_metrics_batch(
    generated_images: List[Image.Image],
    prompts: List[str],
    real_images_dir: Optional[str] = None,
    generated_images_dir: Optional[str] = None
) -> Dict[str, float]:
    """
    Computes a suite of metrics for a batch of generated images.
    
    Args:
        generated_images: List of generated PIL Images.
        prompts: List of corresponding text prompts.
        real_images_dir: Optional path to real images for FID calculation.
        generated_images_dir: Optional path to save generated images for FID calculation.
    
    Returns:
        Dictionary containing 'clip_score', 'fid' (if real dir provided), etc.
    """
    results = {}
    
    # Compute CLIP Score
    if generated_images and prompts:
        try:
            clip_score = compute_clip_score(generated_images, prompts)
            results['clip_score'] = clip_score
            logger.info(f"Computed CLIP Score: {clip_score:.4f}")
        except Exception as e:
            logger.warning(f"CLIP Score computation failed: {e}")
            results['clip_score'] = None
    
    # Compute FID
    if real_images_dir and generated_images_dir:
        try:
            # Ensure generated images are saved if not already in directory
            # The caller is responsible for saving images to generated_images_dir
            # or we can save them here if the list is provided and dir is empty
            if not generated_images_dir or not list(Path(generated_images_dir).iterdir()):
                logger.warning("Generated images directory is empty. Saving batch images.")
                for i, img in enumerate(generated_images):
                    img_path = Path(generated_images_dir) / f"gen_{i:06d}.png"
                    img.save(img_path)
            
            fid_val = compute_fid(real_images_dir, generated_images_dir)
            results['fid'] = fid_val
            logger.info(f"Computed FID Score: {fid_val:.4f}")
        except Exception as e:
            logger.warning(f"FID Score computation failed: {e}")
            results['fid'] = None
    
    return results

def save_metrics_to_json(metrics: Dict[str, float], output_path: str) -> None:
    """
    Saves metrics dictionary to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure paths are strings if they are Path objects inside
    serializable_metrics = {}
    for k, v in metrics.items():
        if isinstance(v, Path):
            serializable_metrics[k] = str(v)
        else:
            serializable_metrics[k] = v
    
    with open(path, 'w') as f:
        json.dump(serializable_metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def load_metrics_from_json(input_path: str) -> Dict[str, float]:
    """
    Loads metrics dictionary from a JSON file.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {input_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def main():
    """
    Main entry point for testing the metrics module.
    This function is intended to be run to verify the module works.
    """
    logger.info("Running metrics module self-test...")
    
    # Test MSE
    t1 = torch.rand(10, 3, 256, 256)
    t2 = t1 + 0.1
    mse = compute_mse(t1, t2)
    logger.info(f"MSE Test: {mse}")
    
    # Test CLIP Score (requires real images and prompts)
    # Creating dummy images for test
    dummy_images = [Image.new('RGB', (224, 224), color='red') for _ in range(2)]
    dummy_prompts = ["a red image", "another red image"]
    try:
        clip_score = compute_clip_score(dummy_images, dummy_prompts)
        logger.info(f"CLIP Score Test: {clip_score}")
    except Exception as e:
        logger.error(f"CLIP Test Failed: {e}")
    
    logger.info("Metrics module test completed.")

if __name__ == "__main__":
    main()