from __future__ import annotations

import json
import logging
import sys
import traceback
import gc
from pathlib import Path
from typing import Dict, List, Optional

import torch
from huggingface_hub import snapshot_download
from llmxive_toolkit import get_logger, paths
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd

log = get_logger(__name__)

try:
    from auto_gptq import AutoGPTQForCausalLM
    _AUTO_GPTQ_AVAILABLE = True
except Exception as exc:
    log.warning("auto-gptq not available (%s); quantization will be skipped.", exc)
    _AUTO_GPTQ_AVAILABLE = False

def _get_calibration_data(parquet_path: Path, tokenizer, num_samples=10, seq_len=2048) -> List[List[int]]:
    """Load samples from WikiText-2 and tokenize them for auto-gptq calibration."""
    if not parquet_path.exists():
        log.error("Calibration data missing at %s", parquet_path)
        return []
    
    df = pd.read_parquet(parquet_path)
    texts = df['text'].dropna().tolist()
    
    examples = []
    for i in range(min(num_samples, len(texts))):
        text = texts[i]
        tokens = tokenizer.encode(text, add_special_tokens=False)
        if len(tokens) < seq_len:
            # Pad or just take as is
            examples.append(tokens)
        else:
            examples.append(tokens[:seq_len])
    return examples

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

def _quantize_model(fp16_dir: Path, bits: int, calibration_path: Path) -> Path | None:
    """Attempt to quantize a FP16 checkpoint to `bits`‑bit precision using auto‑gptq."""
    if not _AUTO_GPTQ_AVAILABLE:
        log.info("Skipping quantization to %d‑bit (auto‑gptq unavailable).", bits)
        return None
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(fp16_dir))
        examples = _get_calibration_data(calibration_path, tokenizer)
        
        # auto-gptq on CPU is limited; we attempt the standard API
        model = AutoGPTQForCausalLM.from_pretrained(
            str(fp16_dir), 
            device_map="cpu", 
            torch_dtype=torch.float16
        )
        
        quantized_dir = fp16_dir.parent / f"{fp16_dir.name}_{bits}bit"
        # Note: quantization usually requires a GPU; this may fail on CI
        model.quantize(examples=examples, bits=bits, save_dir=str(quantized_dir))
        
        log.info("Quantized model to %d‑bit at %s", bits, quantized_dir)
        return quantized_dir
    except Exception as exc:
        log.error("Quantization to %d‑bit failed: %s", bits, exc)
        return None
    finally:
        gc.collect()

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
        "checkpoint_path": str(checkpoint_path.absolute()),
        "load_success": load_success,
        "seed": 42,
    }
    # Fix filename to match gpt-neo-XXXM_quant.json
    config_path = paths.data("configs", f"{model_name}_{quantization}.json")
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    log.info("Wrote config %s", config_path)

def _process_model(spec: Dict[str, str | int], calibration_path: Path) -> None:
    """Download a model, generate configurations for all quantization levels, and write JSON files."""
    repo_id = spec["repo_id"]
    model_name = spec["model_name"]
    model_size_m = spec["model_size_m"]
    base_dir = paths.data("models", model_name, "fp16")

    try:
        fp16_dir = _download_model(repo_id, base_dir)
        fp16_success = True
    except Exception:
        fp16_dir = base_dir / "missing_fp16"
        fp16_dir.mkdir(parents=True, exist_ok=True)
        fp16_success = False
        log.error("Proceeding with missing FP16 checkpoint for %s", model_name)

    _write_config(model_name, model_size_m, "fp16", fp16_dir, load_success=fp16_success)

    for bits in (8, 4):
        quant_dir = _quantize_model(fp16_dir, bits, calibration_path)
        quant_name = "int8" if bits == 8 else "4bit"
        success = quant_dir is not None
        checkpoint_path = quant_dir if quant_dir else fp16_dir
        _write_config(model_name, model_size_m, quant_name, checkpoint_path, load_success=success)

def _attempt_llama_oom():
    """Attempt to load a 7B model to trigger and log OOM on edge-class CPUs."""
    log_path = paths.path("logs", "model_load.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    repo_id = "NousResearch/Llama-2-7b-hf"
    log.info("Attempting to load %s to verify OOM handling...", repo_id)
    try:
        # Attempt to load in FP16 to maximize memory pressure
        AutoModelForCausalLM.from_pretrained(
            repo_id, 
            torch_dtype=torch.float16, 
            device_map="cpu"
        )
        log.info("Unexpectedly succeeded in loading 7B model.")
    except Exception as e:
        error_msg = f"OOM or Load Error for {repo_id}: {str(e)}\n"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(error_msg)
        log.info("Successfully logged OOM/Load failure for 7B model.")

def main(argv: List[str] | None = None) -> int:
    """Iterate over model specs, download, quantize, and write configs."""
    calibration_path = paths.data("raw", "wikitext2.parquet")
    
    specs = [
        {"repo_id": "EleutherAI/gpt-neo-125M", "model_name": "gpt-neo-125M", "model_size_m": 125},
        {"repo_id": "EleutherAI/gpt-neo-350M", "model_name": "gpt-neo-350M", "model_size_m": 350},
        {"repo_id": "EleutherAI/gpt-neo-1.3B", "model_name": "gpt-neo-1.3B", "model_size_m": 1300},
    ]

    overall_success = True
    for spec in specs:
        try:
            _process_model(spec, calibration_path)
        except Exception:
            log.error("Failed processing %s", spec["model_name"])
            traceback.print_exc()
            overall_success = False
    
    # Requirement: Log OOM attempts for 7B models
    try:
        _attempt_llama_oom()
    except Exception as e:
        log.error("Error during OOM attempt: %s", e)
        overall_success = False

    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())