"""
src/data/latent_generator.py

Generate visual‑layout latents for each document using a frozen
``layoutlmv3-base`` encoder. The script is CPU‑only and writes the
resulting parquet file as well as a small runtime log.

Expected CLI (as used in quickstart.md):
    python -m src.data.latent_generator \
        --input-parquet <input.parquet> \
        --output-parquet <output.parquet> \
        --encoder-name layoutlmv3-base \
        --device cpu
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from transformers import AutoFeatureExtractor, AutoModel

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate visual layout latents using a frozen LayoutLMv3 encoder."
    )
    parser.add_argument(
        "--input-parquet",
        type=Path,
        required=True,
        help="Path to the parquet file containing DocumentPair records (must include 'image_path').",
    )
    parser.add_argument(
        "--output-parquet",
        type=Path,
        required=True,
        help="Path where the output parquet with the added 'visual_latent' column will be written.",
    )
    parser.add_argument(
        "--encoder-name",
        type=str,
        default="layoutlmv3-base",
        help="HuggingFace model identifier for the frozen visual encoder.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device on which to run inference. Only 'cpu' is supported in the CI environment.",
    )
    return parser.parse_args(argv)

def load_encoder(encoder_name: str, device: str):
    """
    Load the frozen LayoutLMv3 model and its feature extractor on the specified device.
    The model is loaded in ``torch.no_grad()`` mode and with ``map_location='cpu'`` to
    guarantee CPU‑only execution. If the model cannot be loaded on CPU, a clear
    RuntimeError is raised.
    """
    if device != "cpu":
        raise RuntimeError(
            "Frozen visual encoder cannot be loaded on non‑CPU devices in this pipeline."
        )
    try:
        log.info(f"Loading feature extractor for {encoder_name}...")
        feature_extractor = AutoFeatureExtractor.from_pretrained(encoder_name)

        log.info(f"Loading LayoutLMv3 model {encoder_name} on CPU...")
        model = AutoModel.from_pretrained(encoder_name, trust_remote_code=True, torch_dtype=torch.float32)
        model.to("cpu")
        model.eval()
        return feature_extractor, model
    except Exception as e:
        raise RuntimeError(
            "Frozen visual encoder cannot be loaded on CPU – incompatibility"
        ) from e

def encode_image(image_path: Path, feature_extractor, model):
    """
    Run a single image through the frozen encoder and return a 768‑dim numpy array.
    """
    image = Image.open(image_path).convert("RGB")
    inputs = feature_extractor(images=image, return_tensors="pt")
    inputs = {k: v.to("cpu") for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        # ``pooler_output`` is a (1, hidden_dim) tensor; layoutlmv3 uses 768 hidden size.
        latent = outputs.pooler_output.squeeze(0).cpu().numpy()
    return latent

def main(argv=None):
    args = parse_args(argv)

    start_time = time.time()
    log.info("Reading input parquet...")
    df = pd.read_parquet(args.input_parquet)

    required_cols = {"image_path"}
    missing = required_cols - set(df.columns)
    if missing:
        raise RuntimeError(f"Input parquet is missing required columns: {missing}")

    # Load encoder once
    feature_extractor, model = load_encoder(args.encoder_name, args.device)

    # Prepare a list to hold the latents
    latents = []

    log.info(f"Generating latents for {len(df)} documents...")
    for idx, row in df.iterrows():
        image_path = Path(row["image_path"])
        if not image_path.is_file():
            raise RuntimeError(f"Image file does not exist: {image_path}")

        latent = encode_image(image_path, feature_extractor, model)

        if latent.shape[0] != 768:
            raise RuntimeError(
                f"Unexpected latent size {latent.shape[0]} for image {image_path}"
            )
        if not (latent == latent).all():  # NaN check
            raise RuntimeError(f"NaN values found in latent for image {image_path}")

        latents.append(latent.tolist())

    # Append the new column
    df = df.copy()
    df["visual_latent"] = latents

    # Verify all rows have correct length
    for i, vec in enumerate(df["visual_latent"]):
        if len(vec) != 768:
            raise RuntimeError(f"Row {i} visual_latent length != 768")
        if any(v is None for v in vec):
            raise RuntimeError(f"Row {i} visual_latent contains None")

    # Write output parquet
    args.output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output_parquet, index=False)

    end_time = time.time()
    elapsed = end_time - start_time
    log.info(f"Latent generation completed in {elapsed:.2f} seconds.")

    # Record runtime
    runtime_path = paths.results("runtime", "latent_inference_seconds.txt")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    with open(runtime_path, "w") as f:
        f.write(f"{elapsed:.2f}\\n")

    log.info(f"Runtime written to {runtime_path}")

if __name__ == "__main__":
    main()
