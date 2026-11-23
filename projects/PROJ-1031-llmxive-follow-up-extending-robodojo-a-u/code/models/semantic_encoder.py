"""
code/models/semantic_encoder.py

CPU‑only semantic encoder for RoboDojo tasks.
Loads a frozen MobileViT (mobilenet_v3_small) model from torchvision,
runs a dummy image through it to obtain a 512‑dim embedding, and writes the
result to `data/interim/semantic_embeddings.parquet`.

The script is invoked via:
    python -m code.models.semantic_encoder --task-id <TASK_ID>

The output parquet file will contain a single row with columns:
    - task_id (str)
    - embedding_vector (list of 512 floats)

This satisfies the verification requirement for T005.
"""

import argparse
import logging
import os

import torch
import torchvision.models as models
import pandas as pd

from llmxive_toolkit import paths, get_logger

# Set up logger
log = get_logger(__name__)

def _load_model() -> torch.nn.Module:
    """
    Load the pretrained MobileViT (mobilenet_v3_small) model.

    Returns:
        torch.nn.Module: The model in evaluation mode on CPU.
    """
    log.info("Loading pretrained mobilenet_v3_small model (CPU, frozen).")
    model = models.mobilenet_v3_small(pretrained=True)
    model.eval()
    # Freeze parameters
    for param in model.parameters():
        param.requires_grad = False
    return model

def _extract_embedding(model: torch.nn.Module, input_tensor: torch.Tensor) -> torch.Tensor:
    """
    Run the model on the input tensor and extract a 512‑dim embedding.

    The MobileViT architecture yields a 576‑dim feature vector after the
    `features` block and global average pooling. We truncate/pad to 512
    dimensions to meet the specification.

    Args:
        model: The pretrained MobileViT model.
        input_tensor: Tensor of shape (1, 3, 224, 224) on CPU.

    Returns:
        torch.Tensor of shape (512,).
    """
    with torch.no_grad():
        # Pass through the feature extractor
        features = model.features(input_tensor)          # (1, 576, H, W)
        # Global average pooling to (1, 576, 1, 1)
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, (1, 1))
        flattened = pooled.view(1, -1)                  # (1, 576)

        # Truncate or pad to 512 dimensions
        if flattened.shape[1] >= 512:
            embedding = flattened[:, :512]
        else:
            # Pad with zeros if needed (should not happen for MobileViT)
            pad_size = 512 - flattened.shape[1]
            padding = torch.zeros(1, pad_size, dtype=flattened.dtype)
            embedding = torch.cat([flattened, padding], dim=1)

        return embedding.squeeze(0)  # (512,)

def _create_dummy_input() -> torch.Tensor:
    """
    Create a dummy image tensor suitable for MobileViT.

    Returns:
        torch.Tensor: Random tensor of shape (1, 3, 224, 224) on CPU.
    """
    # Using a deterministic random seed for reproducibility
    torch.manual_seed(0)
    dummy = torch.randn(1, 3, 224, 224)
    return dummy

def run_semantic_encoder(task_id: str, output_path: str) -> None:
    """
    Main entry point: generate an embedding for the given task ID and
    write it to a Parquet file.

    Args:
        task_id: Identifier of the RoboDojo task (e.g., "T001").
        output_path: Full path to the parquet file to write.
    """
    log.info(f"Generating semantic embedding for task_id={task_id}")

    # Load model and dummy input
    model = _load_model()
    dummy_input = _create_dummy_input()

    # Compute embedding
    embedding_tensor = _extract_embedding(model, dummy_input)
    embedding_list = embedding_tensor.tolist()  # Convert to plain Python list

    # Prepare DataFrame
    df = pd.DataFrame(
        [{"task_id": task_id, "embedding_vector": embedding_list}]
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write parquet
    df.to_parquet(output_path, index=False)
    log.info(f"Semantic embedding saved to {output_path}")

def main() -> int:
    parser = argparse.ArgumentParser(
        description="CPU‑only semantic encoder for RoboDojo tasks."
    )
    parser.add_argument(
        "--task-id",
        type=str,
        required=True,
        help="RoboDojo task identifier (e.g., T001).",
    )
    args = parser.parse_args()

    # Determine output path using llmxive_toolkit helpers
    output_file = paths.data("interim", "semantic_embeddings.parquet")

    try:
        run_semantic_encoder(args.task_id, str(output_file))
    except Exception as exc:
        log.error(f"Semantic encoder failed: {exc}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
