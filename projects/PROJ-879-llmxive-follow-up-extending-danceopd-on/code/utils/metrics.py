"""
Utility functions for computing image‑text similarity (CLIP score) and
Fréchet Inception Distance (FID) between two sets of images.  Implemented
for CPU‑only execution using the ViT‑B/32 CLIP model from HuggingFace
and the `torch‑fidelity` library.

The functions are deliberately lightweight and avoid any GPU usage.
They are used by the fidelity‑evaluation steps of the research pipeline.
"""

from pathlib import Path
from typing import Union, List

import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# torch‑fidelity provides a high‑level API to compute FID.
# It works with directories containing image files.
from torch_fidelity import calculate_metrics

# Global CLIP model and processor instantiated once to avoid repeated loading.
_clip_model: CLIPModel = None
_clip_processor: CLIPProcessor = None


def _load_clip_model() -> None:
    """
    Load the CLIP ViT‑B/32 model and processor onto CPU.
    This helper is called lazily by the public functions.
    """
    global _clip_model, _clip_processor
    if _clip_model is None or _clip_processor is None:
        # Explicitly request the CPU device.
        _clip_model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32",
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        _clip_model.eval()
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def _load_image(image: Union[str, Path, Image.Image]) -> Image.Image:
    """
    Helper to open an image from a path or pass through an already opened PIL.Image.

    Args:
        image: Path‑like object or a PIL.Image instance.

    Returns:
        A PIL.Image in RGB mode.
    """
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    # Assume path‑like
    img_path = Path(image)
    if not img_path.exists():
        raise FileNotFoundError(f"Image file not found: {img_path}")
    with Image.open(img_path) as img:
        return img.convert("RGB")


def calculate_clip_score(image: Union[str, Path, Image.Image], text: str) -> float:
    """
    Compute the cosine similarity between a CLIP image embedding and a CLIP text
    embedding using the ViT‑B/32 model (CPU‑only).

    Args:
        image: Path to an image file or a PIL.Image object.
        text:  Text prompt to compare against the image.

    Returns:
        A float in the range [-1, 1] representing cosine similarity. Higher is
        more similar.
    """
    _load_clip_model()
    img = _load_image(image)

    # Tokenise and encode
    inputs = _clip_processor(
        text=[text],
        images=img,
        return_tensors="pt",
        padding=True,
    )

    # Move tensors to CPU explicitly (model is already on CPU)
    with torch.no_grad():
        image_embeds = _clip_model.get_image_features(**{
            k: v.to("cpu") for k, v in inputs.items() if k.startswith("pixel_values")
        })
        text_embeds = _clip_model.get_text_features(**{
            k: v.to("cpu") for k, v in inputs.items() if k.startswith("input_ids")
        })

    # Normalise embeddings
    image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
    text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)

    # Cosine similarity is a dot product of normalised vectors
    similarity = torch.nn.functional.cosine_similarity(image_embeds, text_embeds).item()
    return float(similarity)


def calculate_fid(reference_dir: Union[str, Path], generated_dir: Union[str, Path]) -> float:
    """
    Compute the Fréchet Inception Distance (FID) between two collections of images.

    The function expects two directories, each containing image files (any format
    supported by Pillow).  It delegates the heavy lifting to ``torch_fidelity``,
    which internally loads an Inception‑v3 classifier and computes the statistic.

    Args:
        reference_dir: Path to the directory with ground‑truth images.
        generated_dir: Path to the directory with images produced by the model.

    Returns:
        The FID score as a float.  Lower values indicate higher similarity.

    Raises:
        FileNotFoundError: If either directory does not exist or contains no
                           image files.
    """
    ref_path = Path(reference_dir)
    gen_path = Path(generated_dir)

    if not ref_path.is_dir():
        raise FileNotFoundError(f"Reference directory not found: {ref_path}")
    if not gen_path.is_dir():
        raise FileNotFoundError(f"Generated images directory not found: {gen_path}")

    # ``torch_fidelity`` expects the inputs as strings or pathlib objects.
    # We explicitly request the CPU device to respect the CPU‑only constraint.
    metrics = calculate_metrics(
        input1=str(ref_path),
        input2=str(gen_path),
        fid=True,
        device="cpu",
    )

    # The returned dict contains a key ``fid`` when ``fid=True``.
    fid_score = metrics.get("fid")
    if fid_score is None:
        raise RuntimeError("FID computation failed; torch_fidelity did not return a score.")
    return float(fid_score)


__all__ = [
    "calculate_clip_score",
    "calculate_fid",
]