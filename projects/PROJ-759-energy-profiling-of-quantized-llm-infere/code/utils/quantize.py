from __future__ import annotations

import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Dict, List

from huggingface_hub import snapshot_download
from auto_gptq import AutoGPTQForCausalLM

from llmxive_toolkit import get_logger

log = get_logger(__name__)

def _download_model(repo_id: str, target_dir: Path) -> Path:
    """Download a HuggingFace model repository to target_dir."""
    try:
        path = snapshot_download(repo_id, local_dir=target_dir, local_dir_use_symlinks=False)
        log.info("Downloaded model %s to %s", repo_id, path)
        return Path(path)
    except Exception as exc:
        log.error("Failed to download model %s: %s", repo_id, exc)
        raise

def _quantize_model(fp16_dir: Path, bits: int) -> Path | None:
    """Attempt to quantize a FP16 checkpoint to bits‑bit precision using auto_gptq."""
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
    fp16_dir = _download_model(repo_id, base_dir)

    # Write FP16 config
    _write_config(model_name, model_size_m, "fp16", fp16_dir, load_success=True)

    for bits in (8, 4):
        quant_dir = _quantize_model(fp16_dir, bits)
        quant_name = "int8" if bits == 8 else "4bit"
        success = quant_dir is not None
        _write_config(
            model_name,
            model_size_m,
            quant_name,
            quant_dir if quant_dir else fp16_dir,
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

    for spec in specs:
        try:
            _process_model(spec)
        except Exception:
            log.error("Failed processing %s", spec["model_name"])
            traceback.print_exc()
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())