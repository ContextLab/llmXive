from __future__ import annotations

import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Dict, List

from huggingface_hub import snapshot_download
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Attempt to import the auto-gptq quantizer. If unavailable (e.g., missing torch),
# we will skip the actual quantization step but still generate configuration files.
try:
    from auto_gptq import AutoGPTQForCausalLM  # type: ignore
    _AUTO_GPTQ_AVAILABLE = True
except Exception as exc:  # pragma: no cover
    log.warning("auto-gptq not available (%s); quantization will be skipped.", exc)
    _AUTO_GPTQ_AVAILABLE = False

def _download_model(repo_id: str, target_dir: Path) -> Path:
    """Download a HuggingFace model repository to target_dir."""
    try:
        path = snapshot_download(
            repo_id, local_dir=target_dir, local_dir_use_symlinks=False
        )
        log.info("Downloaded model %s to %s", repo_id, path)
        return Path(path)
    except Exception as exc:
        log.error("Failed to download model %s: %s", repo_id, exc)
        raise

def _quantize_model(fp16_dir: Path, bits: int) -> Path | None:
    """Attempt to quantize a FP16 checkpoint to `bits`‑bit precision using auto‑gptq."""
    if not _AUTO_GPTQ_AVAILABLE:
        log.info("Skipping quantization to %d‑bit (auto‑gptq unavailable).", bits)
        return None
    try:
        model = AutoGPTQForCausalLM.from_pretrained(str(fp16_dir), device="cpu")
        quantized_dir = fp16_dir.parent / f"{fp16_dir.name}_{bits}bit"
        model.quantize(bits=bits, save_dir=str(quantized_dir))
        log.info("Quantized model to %d‑bit at %s", bits, quantized_dir)
        return quantized_dir
    except Exception as exc:
        log.error("Quantization to %d‑bit failed: %s", bits, exc)
        return None

def _write_config(
    model_name: str,
    model_size_m: int,
    quantization: str,
    checkpoint_path: Path,
    load_success: bool,
) -> None:
    """Write a JSON configuration file compatible with contracts/config.schema.yaml."""
    config = {
        "model_name": model_name,
        "model_size_m": model_size_m,
        "quantization": quantization,
        "checkpoint_path": str(checkpoint_path),
        "load_success": load_success,
        "seed": 42,
    }
    config_path = Path("data") / "configs" / f"{model_name}_{quantization}.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    log.info("Wrote config %s", config_path)

def _process_model(spec: Dict[str, str | int]) -> None:
    """Download a model, generate configurations for all quantization levels, and write JSON files."""
    repo_id = spec["repo_id"]
    model_name = spec["model_name"]
    model_size_m = spec["model_size_m"]
    base_dir = Path("data") / "models" / model_name / "fp16"

    # Attempt to download the FP16 checkpoint. If it fails, we still produce a config
    # indicating load_failure.
    try:
        fp16_dir = _download_model(repo_id, base_dir)
        fp16_success = True
    except Exception:
        fp16_dir = base_dir / "missing_fp16"
        fp16_dir.mkdir(parents=True, exist_ok=True)
        fp16_success = False
        log.error("Proceeding with missing FP16 checkpoint for %s", model_name)

    # Write FP16 config (always mark success based on download outcome)
    _write_config(
        model_name,
        model_size_m,
        "fp16",
        fp16_dir,
        load_success=fp16_success,
    )

    # Generate INT8 and 4‑bit configs
    for bits in (8, 4):
        quant_dir = _quantize_model(fp16_dir, bits)
        quant_name = "int8" if bits == 8 else "4bit"
        # If quantization failed or auto‑gptq unavailable, we fall back to the FP16 path
        success = quant_dir is not None
        checkpoint_path = quant_dir if quant_dir else fp16_dir
        _write_config(
            model_name,
            model_size_m,
            quant_name,
            checkpoint_path,
            load_success=success,
        )

def main(argv: List[str] | None = None) -> int:
    """Iterate over model specs, download, quantize, and write configs."""
    specs = [
        {
            "repo_id": "EleutherAI/gpt-neo-125M",
            "model_name": "gpt-neo-125M",
            "model_size_m": 125,
        },
        {
            "repo_id": "EleutherAI/gpt-neo-350M",
            "model_name": "gpt-neo-350M",
            "model_size_m": 350,
        },
        {
            "repo_id": "EleutherAI/gpt-neo-1.3B",
            "model_name": "gpt-neo-1.3B",
            "model_size_m": 1300,
        },
    ]

    overall_success = True
    for spec in specs:
        try:
            _process_model(spec)
        except Exception:
            log.error("Failed processing %s", spec["model_name"])
            traceback.print_exc()
            overall_success = False
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
