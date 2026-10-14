"""
quantize.py
===========

This module downloads GPT‑Neo model checkpoints, attempts to generate INT8
and 4‑bit quantized variants using **auto‑gptq**, and writes a configuration
JSON file for each variant (including the FP16 baseline) under
``data/configs/``.  The JSON files conform to ``contracts/config.schema.yaml``.

The script is intended to be run as a stand‑alone command:

.. code-block:: bash

    python code/utils/quantize.py

It will:

1. Download the three GPT‑Neo model checkpoints from the HuggingFace Hub
   (``EleutherAI/gpt-neo-125M``, ``EleutherAI/gpt-neo-350M``,
   ``EleutherAI/gpt-neo-1.3B``) into ``data/models/``.
2. For each model, write a **FP16** configuration that points to the original
   checkpoint (this always succeeds).
3. Attempt to quantize the checkpoint to **INT8** (8‑bit) and **4‑bit**
   using ``auto_gptq``.  If the quantization succeeds, the quantized
   checkpoint is saved and ``load_success`` is set to ``true``; otherwise,
   the exception is logged, ``load_success`` is ``false`` and the
   configuration still points to the original FP16 checkpoint (so the JSON
   validates against the schema).
4. Emit one JSON file per model‑quantization combination, named
   ``gptneo-<size>_<quant>.json`` (e.g. ``gptneo-125M_int8.json``).

The implementation is deliberately defensive: any exception raised during
download or quantization is caught, logged, and results in a configuration
with ``load_success: false`` – this satisfies the contract while avoiding
OOM crashes that would abort the pipeline.

Dependencies
------------
* ``transformers`` – for model handling (downloaded via ``huggingface_hub``).
* ``huggingface_hub`` – to fetch the model repository.
* ``auto-gptq`` – to perform INT8 / 4‑bit quantization.
* ``torch`` – required by ``auto-gptq`` (CPU‑only).

All new dependencies are added to ``requirements.txt`` in the same
artifact list.

"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Dict, List

from llmxive_toolkit import get_logger, paths

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
log: logging.Logger = get_logger(__name__)

# Mapping from model size (in millions) to HuggingFace repository ID
MODEL_SPECS: List[Dict[str, str | int]] = [
    {
        "model_name": "gpt-neo-125M",
        "model_size_m": 125,
        "repo_id": "EleutherAI/gpt-neo-125M",
    },
    {
        "model_name": "gpt-neo-350M",
        "model_size_m": 350,
        "repo_id": "EleutherAI/gpt-neo-350M",
    },
    {
        "model_name": "gpt-neo-1.3B",
        "model_size_m": 1300,
        "repo_id": "EleutherAI/gpt-neo-1.3B",
    },
]

QUANTIZATION_LEVELS: List[str] = ["fp16", "int8", "4bit"]
SEED: int = 42  # deterministic seed used for all generated configs


# ----------------------------------------------------------------------
# Core functionality
# ----------------------------------------------------------------------
def _download_model(repo_id: str, target_dir: Path) -> Path:
    """
    Download a HuggingFace model repository to ``target_dir`` using
    ``huggingface_hub.snapshot_download``.  The function returns the
    absolute path to the downloaded checkpoint directory.

    Parameters
    ----------
    repo_id: str
        The HuggingFace repository identifier (e.g. ``EleutherAI/gpt-neo-125M``).
    target_dir: Path
        Directory under which the model should be placed.

    Returns
    -------
    Path
        Path to the root of the downloaded model repository.
    """
    from huggingface_hub import snapshot_download

    log.info("Downloading model %s into %s", repo_id, target_dir)
    # ``snapshot_download`` returns the directory containing the repo.
    model_path: Path = Path(
        snapshot_download(repo_id=repo_id, local_dir=str(target_dir), resume_download=True)
    )
    log.info("Model %s downloaded to %s", repo_id, model_path)
    return model_path


def _quantize_model(fp16_dir: Path, bits: int) -> Path | None:
    """
    Attempt to quantize a FP16 checkpoint to ``bits``‑bit precision using
    ``auto_gptq``.  The quantized checkpoint is saved next to the original
    directory with a suffix ``_{bits}bit`` (e.g. ``.../gpt-neo-125M_4bit``).

    If quantization fails (e.g. due to OOM), ``None`` is returned.

    Parameters
    ----------
    fp16_dir: Path
        Directory containing the original FP16 model.
    bits: int
        Target bit‑width (8 or 4).

    Returns
    -------
    Path | None
        Path to the quantized checkpoint if successful, otherwise ``None``.
    """
    try:
        from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
        import torch

        log.info("Starting %d‑bit quantization for %s", bits, fp16_dir)

        # Load the FP16 model in CPU memory
        model = AutoGPTQForCausalLM.from_pretrained(
            str(fp16_dir), device="cpu", torch_dtype=torch.float16
        )

        # ``bits`` must be either 8 or 4 for our use‑case
        quant_cfg = BaseQuantizeConfig(bits=bits, group_size=128, desc_act=False)

        # Perform the quantization – this may raise MemoryError or RuntimeError
        model.quantize(quant_cfg)

        # Save the quantized model
        quant_dir = fp16_dir.parent / f"{fp16_dir.name}_{bits}bit"
        model.save_quantized(str(quant_dir))
        log.info("Quantization to %d‑bit succeeded, saved to %s", bits, quant_dir)
        return quant_dir
    except Exception as exc:
        # Log the full traceback – the caller will mark ``load_success`` as false
        log.error(
            "Quantization to %d‑bit failed for %s: %s",
            bits,
            fp16_dir,
            "".join(traceback.format_exception_only(type(exc), exc)).strip(),
        )
        log.debug(traceback.format_exc())
        return None


def _write_config(
    model_name: str,
    model_size_m: int,
    quantization: str,
    checkpoint_path: Path,
    load_success: bool,
) -> None:
    """
    Write a JSON configuration file compatible with ``contracts/config.schema.yaml``.
    The file is placed under ``data/configs/`` and named
    ``gptneo-<size>_<quant>.json`` (e.g. ``gptneo-125M_int8.json``).

    Parameters
    ----------
    model_name: str
        Human readable identifier (e.g. ``gpt-neo-125M``).
    model_size_m: int
        Model size in millions of parameters.
    quantization: str
        One of ``fp16``, ``int8``, ``4bit``.
    checkpoint_path: Path
        Absolute path to the (quantized) checkpoint directory.
    load_success: bool
        ``true`` if the checkpoint could be loaded without OOM; otherwise ``false``.
    """
    config = {
        "model_name": model_name,
        "model_size_m": model_size_m,
        "quantization": quantization,
        "seed": SEED,
        "checkpoint_path": str(checkpoint_path.resolve()),
        "load_success": load_success,
    }

    # Resolve the output path via the llmxive_toolkit helper (creates the folder)
    out_path = paths.data("configs", f"{model_name}_{quantization}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, sort_keys=True)

    log.info("Wrote configuration %s (load_success=%s)", out_path, load_success)


def _process_model(spec: Dict[str, str | int]) -> None:
    """
    Download a model, generate configurations for all quantization levels,
    and write the corresponding JSON files.
    """
    model_name: str = spec["model_name"]  # type: ignore[assignment]
    model_size_m: int = int(spec["model_size_m"])  # type: ignore[assignment]
    repo_id: str = spec["repo_id"]  # type: ignore[assignment]

    # Directory where the original FP16 checkpoint will live
    fp16_dir = paths.data("models", model_name, "fp16")
    fp16_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1️⃣  Download the FP16 checkpoint (always succeeds unless network error)
    # ------------------------------------------------------------------
    try:
        downloaded_path = _download_model(repo_id, fp16_dir)
        # The checkpoint can be loaded – mark success for FP16
        _write_config(
            model_name=model_name,
            model_size_m=model_size_m,
            quantization="fp16",
            checkpoint_path=downloaded_path,
            load_success=True,
        )
    except Exception as exc:
        # If the download fails we cannot continue – raise to abort the script
        log.error("Failed to download %s: %s", repo_id, exc)
        raise

    # ------------------------------------------------------------------
    # 2️⃣  INT8 quantization
    # ------------------------------------------------------------------
    int8_dir = _quantize_model(fp16_dir, bits=8)
    if int8_dir is not None:
        _write_config(
            model_name=model_name,
            model_size_m=model_size_m,
            quantization="int8",
            checkpoint_path=int8_dir,
            load_success=True,
        )
    else:
        # Fallback – use the FP16 checkpoint path but flag load_success=False
        _write_config(
            model_name=model_name,
            model_size_m=model_size_m,
            quantization="int8",
            checkpoint_path=fp16_dir,
            load_success=False,
        )

    # ------------------------------------------------------------------
    # 3️⃣  4‑bit quantization
    # ------------------------------------------------------------------
    fourbit_dir = _quantize_model(fp16_dir, bits=4)
    if fourbit_dir is not None:
        _write_config(
            model_name=model_name,
            model_size_m=model_size_m,
            quantization="4bit",
            checkpoint_path=fourbit_dir,
            load_success=True,
        )
    else:
        _write_config(
            model_name=model_name,
            model_size_m=model_size_m,
            quantization="4bit",
            checkpoint_path=fp16_dir,
            load_success=False,
        )

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """
    Iterate over the three GPT‑Neo model specifications, download the base
    checkpoint, attempt quantization, and write configuration JSON files.

    The function returns ``0`` on success, ``1`` on fatal error (e.g. network
    failure while downloading a model).
    """
    try:
        for spec in MODEL_SPECS:
            _process_model(spec)
        log.info("All configurations written successfully.")
        return 0
    except Exception as exc:
        log.error("Quantization pipeline terminated with error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
