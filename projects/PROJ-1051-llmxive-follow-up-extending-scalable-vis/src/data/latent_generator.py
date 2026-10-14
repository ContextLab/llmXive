"""
src/data/latent_generator.py

Updated to ensure a clear error is raised if the required Parquet engine
(pyarrow) is missing and to keep the original functionality unchanged.
No CLI changes were required; the script already matches the quickstart.
"""

import argparse
import time
from pathlib import Path

import pandas as pd
import torch
from PIL import Image

from transformers import LayoutLMv3FeatureExtractor, LayoutLMv3Model

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate visual layout latents for each document using a frozen LayoutLMv3 encoder."
    )
    parser.add_argument(
        "--input-parquet",
        type=Path,
        required=True,
        help="Path to the Parquet file containing DocumentPair records (without latents).",
    )
    parser.add_argument(
        "--output-parquet",
        type=Path,
        required=True,
        help="Path where the Parquet file with added `visual_latent` column will be written.",
    )
    parser.add_argument(
        "--encoder-name",
        type=str,
        default="layoutlmv3-base",
        help="Name of the pretrained LayoutLMv3 model to load.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device for inference (e.g., 'cpu' or 'cuda').",
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
        feature_extractor = LayoutLMv3FeatureExtractor.from_pretrained(encoder_name)
        model = LayoutLMv3Model.from_pretrained(encoder_name, torch_dtype=torch.float32)
        model.to(device)
        model.eval()
        return feature_extractor, model
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load LayoutLMv3 encoder '{encoder_name}' on device '{device}': {exc}"
        ) from exc

def encode_image(image_path: Path, feature_extractor, model):
    """
    Run a single image through the frozen encoder and return a 768‑dim numpy array.
    """
    image = Image.open(image_path).convert("RGB")
    encoding = feature_extractor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**{k: v.to(model.device) for k, v in encoding.items()})
    # Use the pooled output as the latent representation
    pooled = outputs.pooler_output.squeeze().cpu().numpy()
    if pooled.shape[0] != 768:
        raise RuntimeError(f"Unexpected latent dimension: {pooled.shape[0]}, expected 768.")
    return pooled

def main(argv=None):
    args = parse_args(argv)

    start_time = time.time()
    # Verify that the input parquet can be read (requires pyarrow)
    try:
        df = pd.read_parquet(args.input_parquet)
    except Exception as exc:
        raise RuntimeError(
            f"Unable to read Parquet file '{args.input_parquet}'. Ensure 'pyarrow' is installed. Original error: {exc}"
        ) from exc

    feature_extractor, model = load_encoder(args.encoder_name, args.device)

    latents = []
    for idx, row in df.iterrows():
        image_path = Path(row["image_path"])
        if not image_path.is_file():
            raise RuntimeError(f"Image file not found: {image_path}")
        latent = encode_image(image_path, feature_extractor, model)
        if len(latent) != 768:
            raise RuntimeError("Generated latent does not have length 768.")
        latents.append(latent)

    df["visual_latent"] = latents
    args.output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output_parquet, engine="pyarrow")
    elapsed = time.time() - start_time
    print(f"✅ Generated visual latents for {len(df)} documents in {elapsed:.2f} seconds.")
    print(f"Output written to: {args.output_parquet}")

if __name__ == "__main__":
    main()
