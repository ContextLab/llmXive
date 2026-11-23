"""
Semantic similarity utility for the cognitive‑load comparison study.

The function computes a visual similarity score between two raster images
using a pretrained ResNet‑18 backbone (CPU‑only).  The similarity is the
cosine similarity of the 512‑dimensional feature vectors extracted from
the network's penultimate layer.  The score lies in the range ``[-1, 1]``;
values close to ``1`` indicate near‑identical images.

For the study the required threshold is ``0.95`` – a trial passes the
semantic check when the similarity score meets or exceeds this value.
"""

import argparse
import json
from pathlib import Path

import torch
import torch.nn.functional as F
import torchvision.transforms as T
from torchvision import models

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: feature extractor based on ResNet‑18 with the final classification
# layer replaced by an identity mapping so that we obtain the 512‑dim
# embedding after the global average‑pooling layer.
# ----------------------------------------------------------------------
_DEVICE = torch.device("cpu")

def _build_model() -> torch.nn.Module:
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    # Replace the final fully‑connected layer with an identity to expose
    # the 512‑dim feature vector.
    model.fc = torch.nn.Identity()
    model.eval()
    model.to(_DEVICE)
    return model

_MODEL = _build_model()

_TRANSFORM = T.Compose(
    [
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)

def _load_image(image_path: Path) -> torch.Tensor:
    """Load an image file and return a pre‑processed tensor."""
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    return _TRANSFORM(img).unsqueeze(0).to(_DEVICE)  # shape: (1, 3, 224, 224)

def compute_similarity(img_path_a: Path, img_path_b: Path) -> float:
    """
    Compute cosine similarity between two images.

    Parameters
    ----------
    img_path_a, img_path_b: Path
        Paths to the two raster images to compare.

    Returns
    -------
    float
        Cosine similarity in ``[-1, 1]`` (higher means more similar).
    """
    with torch.no_grad():
        tensor_a = _load_image(img_path_a)
        tensor_b = _load_image(img_path_b)

        feat_a = _MODEL(tensor_a)  # shape: (1, 512)
        feat_b = _MODEL(tensor_b)

        # Normalise to unit vectors before cosine similarity.
        sim = F.cosine_similarity(feat_a, feat_b).item()
        log.debug(
            "Semantic similarity between %s and %s: %.4f", img_path_a.name, img_path_b.name, sim
        )
        return float(sim)

def _write_validation_record(
    output_path: Path,
    figure_id: str,
    vector_match: bool = False,
    semantic_pass: bool = False,
) -> None:
    """
    Append a ``SemanticValidation`` record.

    This mirrors the schema used by ``vector_match.py`` – both utilities
    write a line with the same keys so that downstream scripts can merge
    them (e.g. ``run_combined_validation.py``).
    """
    record = {
        "figure_id": figure_id,
        "vector_match": vector_match,
        "semantic_pass": semantic_pass,
    }
    with output_path.open("a", encoding="utf-8") as f:
        json.dump(record, f)
        f.write("\n")
    log.debug("Wrote semantic‑validation record for %s", figure_id)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Semantic similarity validation for figure editing trials."
    )
    parser.add_argument(
        "--image-dir-a",
        type=str,
        required=True,
        help="Directory containing the first set of images (e.g., ground‑truth).",
    )
    parser.add_argument(
        "--image-dir-b",
        type=str,
        required=True,
        help="Directory containing the second set of images (e.g., participant outputs).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/validation",
        help="Directory where the ``semantic_validation.jsonl`` file will be written.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Similarity threshold for passing the semantic check.",
    )
    return parser

def main() -> None:
    args = _build_arg_parser().parse_args()
    dir_a = Path(args.image_dir_a)
    dir_b = Path(args.image_dir_b)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    output_file = out_dir / "semantic_validation.jsonl"

    for img_a in dir_a.glob("*.png"):
        figure_id = img_a.stem
        img_b = dir_b / f"{figure_id}.png"
        if not img_b.is_file():
            log.warning("No counterpart image for %s – skipping.", figure_id)
            continue

        try:
            sim = compute_similarity(img_a, img_b)
            passed = sim >= args.threshold
        except Exception as exc:
            log.error("Failed to compute similarity for %s: %s", figure_id, exc)
            passed = False

        _write_validation_record(
            output_file,
            figure_id,
            vector_match=False,  # placeholder – vector_match utility fills this.
            semantic_pass=passed,
        )

    log.info("Semantic similarity validation completed. Records written to %s", output_file)

if __name__ == "__main__":
    main()
