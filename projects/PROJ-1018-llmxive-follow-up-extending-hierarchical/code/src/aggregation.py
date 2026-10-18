"""
Aggregation utilities for HiLS relevance‑score tensors.

The real pipeline writes per‑chunk raw score tensors (saved as ``.pt`` files)
under ``data/interim/raw_scores/``.  This module provides a helper that reads
those tensors, computes the mean across the token dimension for each chunk,
validates the resulting vectors and writes a consolidated JSON file
conforming to the ``RelevanceProfile`` contract.

The implementation is deliberately lightweight – it does not assume a
particular tensor shape beyond ``(N_chunks, N_tokens)`` and works with
PyTorch tensors saved via ``torch.save``.
"""

import os
import json
import logging
from typing import List, Dict, Any

import torch
from src.models import RelevanceProfile

logger = logging.getLogger(__name__)

def _load_tensor(path: str) -> torch.Tensor:
    """Load a single ``.pt`` tensor file."""
    try:
        tensor = torch.load(path, map_location="cpu")
        if not isinstance(tensor, torch.Tensor):
            raise TypeError(f"File {path} does not contain a torch.Tensor")
        return tensor
    except Exception as exc:
        logger.error(f"Failed to load tensor from {path}: {exc}")
        raise

def aggregate_profiles(
    input_dir: str,
    output_path: str,
) -> List[RelevanceProfile]:
    """
    Read all ``.pt`` files in ``input_dir``, compute the mean across the
    token dimension for each chunk and write a JSON array of
    :class:`RelevanceProfile` objects.

    Args:
        input_dir: Directory containing raw score tensors.
        output_path: Destination JSON file (e.g. ``data/interim/relevance_profiles.json``).

    Returns:
        List of ``RelevanceProfile`` instances (also written to ``output_path``).
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory {input_dir} does not exist")

    profiles: List[RelevanceProfile] = []

    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".pt"):
            continue
        full_path = os.path.join(input_dir, fname)
        tensor = _load_tensor(full_path)

        if tensor.dim() != 2:
            raise ValueError(
                f"Tensor {fname} must be 2‑D (chunks × tokens), got shape {tensor.shape}"
            )

        # Compute mean relevance per chunk (dim=1)
        mean_scores = tensor.mean(dim=1).tolist()

        # Derive a deterministic chunk identifier from the filename
        chunk_id = os.path.splitext(fname)[0]

        # We do not have a document identifier at this stage; use a placeholder.
        profile = RelevanceProfile(
            chunk_id=chunk_id,
            scores=mean_scores,
            document_id="unknown",
        )
        profiles.append(profile)

    # Serialize to JSON
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump([p.to_dict() for p in profiles], fp, indent=2)

    logger.info(f"Wrote {len(profiles)} aggregated relevance profiles to {output_path}")
    return profiles
