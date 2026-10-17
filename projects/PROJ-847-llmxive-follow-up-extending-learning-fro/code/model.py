"""Model loader for the density‑supervision study.

This module provides a function to load a real, lightweight pretrained
language model (≤ 100 M parameters) that will serve as the diffusion
denoiser backbone. The default model is ``distilgpt2`` (≈ 82 M
parameters) which runs comfortably on CPU.

The loader also writes a JSON metadata file ``outputs/model_checkpoint.json``
containing the model identifier, parameter count, device, a SHA‑256 hash
of the model's configuration file, and a note explaining the substitution
of the originally‑specified (non‑existent) checkpoint.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import hf_hub_download

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _write_checkpoint_metadata(
    model_id: str, config_path: Path, param_count: int, substitution_note: str
) -> None:
    """Write ``outputs/model_checkpoint.json`` with model metadata."""
    # Compute SHA‑256 of the config file.
    sha256 = hashlib.sha256()
    with config_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    metadata = {
        "model_id": model_id,
        "parameter_count": param_count,
        "device": "cpu",
        "config_sha256": sha256.hexdigest(),
        "substitution_note": substitution_note,
    }
    out_path = paths.outputs("model_checkpoint.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2, sort_keys=True)
    log.info("Wrote model checkpoint metadata to %s", out_path)

def load_diffusion_model(
    model_id: str = "distilgpt2"
) -> AutoModelForCausalLM:
    """Download and load a ≤ 100 M‑parameter diffusion model.

    Parameters
    ----------
    model_id: str, optional
        HuggingFace model identifier. Defaults to ``distilgpt2`` which
        satisfies the ≤ 100 M‑parameter constraint.

    Returns
    -------
    AutoModelForCausalLM
        The loaded model (CPU‑only, evaluation mode).
    """
    # Strip any ``hf://`` prefix for compatibility with the original API.
    if model_id.startswith("hf://"):
        model_id = model_id[len("hf://") :]

    # Load model and tokenizer.
    log.info("Downloading and loading model %s", model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="cpu")
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Verify parameter count.
    param_count = sum(p.numel() for p in model.parameters())
    if param_count > 100_000_000:
        raise ValueError(
            f"Model {model_id} has {param_count:,} parameters, exceeding the 100 M limit."
        )
    log.info("Model loaded on CPU with %d parameters", param_count)

    # Retrieve the config file to compute its SHA‑256.
    config_path = Path(
        hf_hub_download(repo_id=model_id, filename="config.json")
    )

    substitution_note = (
        "Original spec referenced non‑existent checkpoint "
        "`author/lightdiff-100m`; substituted with real HuggingFace "
        f"`{model_id}` (≤ 100 M parameters)."
    )
    _write_checkpoint_metadata(
        model_id=model_id,
        config_path=config_path,
        param_count=param_count,
        substitution_note=substitution_note,
    )

    # Attach tokenizer for downstream use (optional convenience).
    model.tokenizer = tokenizer  # type: ignore[attr-defined]

    log.info("Model loading complete")
    return model