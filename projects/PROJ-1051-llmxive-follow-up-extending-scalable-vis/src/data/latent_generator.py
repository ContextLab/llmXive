"""
src/data/latent_generator.py

Generates a 768‑dim visual layout latent for every document using the
frozen ``layoutlmv3-base`` model. The script reads the DocumentPair parquet
produced by ``src.data.preprocess``, runs inference on CPU, and writes a new
parquet that includes a ``visual_latent`` column (list of 768 floats).
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List

import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm
from transformers import AutoFeatureExtractor, AutoModel

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate visual layout latents for each document using a frozen LayoutLMv3 encoder."
    )
    parser.add_argument(
        "--input-parquet",
        type=Path,
        required=True,
        help="Path to the DocumentPair parquet file (without latents).",
    )
    parser.add_argument(
        "--output-parquet",
        type=Path,
        required=True,
        help="Path where the output parquet (with latents) will be saved.",
    )
    parser.add_argument(
        "--encoder-name",
        type=str,
        default="layoutlmv3-base",
        help="Name of the pretrained LayoutLMv3 model on HuggingFace.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device for inference ('cpu' or 'cuda'). Must be CPU‑only for this project.",
    )
    return parser.parse_args(argv)

def load_encoder(encoder_name: str, device: str):
    """
    Load the frozen LayoutLMv3 model and its feature extractor on the specified device.
    The model is loaded in ``torch.no_grad()`` mode and with ``map_location='cpu'`` to
    guarantee CPU‑only execution. If the model cannot be loaded on CPU, a clear
    RuntimeError is raised.
    """
    try:
        extractor = AutoFeatureExtractor.from_pretrained(encoder_name)
        model = AutoModel.from_pretrained(encoder_name, torch_dtype=torch.float32)
        model.to(device)
        model.eval()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load LayoutLMv3 encoder '{encoder_name}' on device '{device}': {exc}"
        ) from exc

    # Verify that the model runs on CPU; if not, raise an explicit error.
    if device == "cpu" and not next(model.parameters()).is_cuda:
        return extractor, model
    else:
        raise RuntimeError("Frozen visual encoder cannot be loaded on CPU – incompatibility")

def encode_image(image_path: Path, feature_extractor, model):
    """
    Run a single image through the frozen encoder and return a 768‑dim NumPy array.
    """
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as exc:
        raise RuntimeError(f"Failed to open image '{image_path}': {exc}") from exc

    # Prepare inputs for LayoutLMv3 (expects pixel values and bounding boxes)
    # Since we only need a visual representation, we provide a dummy bbox covering the whole image.
    width, height = image.size
    dummy_bbox = [[0, 0, width, height]]
    inputs = feature_extractor(images=image, boxes=dummy_bbox, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        # Use the pooled_output (CLS token) as the visual latent.
        pooled = outputs.pooler_output  # shape (1, hidden_dim)
        latent = pooled.squeeze(0).cpu().numpy()
    if latent.shape[0] != 768:
        raise RuntimeError(f"Unexpected latent dimension {latent.shape[0]} (expected 768).")
    return latent

def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    # Load data
    try:
        df = pd.read_parquet(args.input_parquet, engine="pyarrow")
    except Exception as exc:
        raise RuntimeError(f"Unable to read Parquet file '{args.input_parquet}': {exc}") from exc

    # Load encoder
    extractor, model = load_encoder(args.encoder_name, args.device)

    latents: List[List[float]] = []
    start_time = time.time()
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Generating latents"):
        image_path = Path(row["image_path"])
        latent = encode_image(image_path, extractor, model)
        latents.append(latent.tolist())

    df["visual_latent"] = latents
    args.output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output_parquet, engine="pyarrow")
    elapsed = time.time() - start_time
    log.info(f"✅ Visual latents written to {args.output_parquet} (elapsed {elapsed:.1f}s)")

    # Record runtime for verification
    runtime_path = paths.results("runtime", "latent_inference_seconds.txt")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_path.open("w", encoding="utf-8") as f:
        f.write(str(elapsed))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Latent generation failed: {exc}")
        sys.exit(1)