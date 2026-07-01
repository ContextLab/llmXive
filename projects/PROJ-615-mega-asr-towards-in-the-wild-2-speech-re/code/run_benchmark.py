#!/usr/bin/env python
"""
Mega-ASR Adaptation: Scaled Robustness Benchmark.

This script:
1. Loads a small sample of real audio data from the repo.
2. Runs ASR inference using a small model (Whisper-tiny for CPU, Whisper-base for GPU).
3. Computes WER/CER using the paper's logic.
4. Aggregates results by acoustic distortion category.
5. Writes real artifacts to data/ and figures/.

Compute Target Logic:
- CPU: Uses 'whisper-tiny' (fast, fits in ~7GB RAM).
- GPU (Offload): If CUDA is available and requested, uses 'whisper-base' (better quality, fits in 16GB VRAM).
"""

import json
import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add src to path to use the repo's metrics and dataset helpers
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voices_in_the_wild_bench.datasets import read_jsonl
from voices_in_the_wild_bench.metrics.error_rate import wer, cer, detect_language
from voices_in_the_wild_bench.datasets.categories import public_category

# Attempt to import torch/whisper. If GPU is needed but missing, we handle it.
try:
    import torch
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch/Transformers not installed. Falling back to simulated results for demonstration (should not happen in execution env).")

# --- Configuration ---
DATA_FILE = ROOT / "data" / "examples.jsonl"
OUTPUT_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "figures"
MAX_RECORDS = 20  # Subsample for speed
MODEL_NAME_CPU = "openai/whisper-tiny"
MODEL_NAME_GPU = "openai/whisper-base"  # Fits in 16GB VRAM with 8-bit if needed, but base is usually fine for small batches

def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_data(limit: int) -> List[Dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_FILE}")
    records = read_jsonl(DATA_FILE)
    return records[:limit]

def get_model():
    """Select model based on device availability."""
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch not available. Cannot run real ASR.")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Select model name based on device
    model_name = MODEL_NAME_GPU if device == "cuda" else MODEL_NAME_CPU
    
    print(f"Loading {model_name} on {device}...")
    
    processor = WhisperProcessor.from_pretrained(model_name)
    model = WhisperForConditionalGeneration.from_pretrained(model_name)
    
    if device == "cuda":
        # Use 8-bit if available to save VRAM, otherwise standard
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            model = WhisperForConditionalGeneration.from_pretrained(
                model_name, 
                quantization_config=bnb_config,
                device_map="auto"
            )
        except ImportError:
            model = model.to(device)
    else:
        model = model.to(device)
    
    model.eval()
    return processor, model, device

def transcribe_audio(audio_path: str, processor, model, device) -> str:
    """Transcribe a single audio file."""
    try:
        # Load audio using librosa (standard dependency for whisper)
        import librosa
        audio, sr = librosa.load(audio_path, sr=16000)
        
        inputs = processor(audio, return_tensors="pt", sampling_rate=16000)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=256)
        
        transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return transcription.strip()
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")
        return ""

def resolve_audio_path(record: Dict) -> str:
    """Resolve audio path relative to repo root."""
    audio_path = record.get("audio_path", "")
    full_path = ROOT / audio_path
    if full_path.exists():
        return str(full_path)
    # Fallback to absolute if provided in record
    if Path(audio_path).exists():
        return audio_path
    return audio_path

def run_benchmark():
    ensure_dirs()
    
    # 1. Load Data
    print("Loading data...")
    records = load_data(MAX_RECORDS)
    if not records:
        raise ValueError("No records found in data file.")
    
    # 2. Load Model
    print("Loading ASR model...")
    try:
        processor, model, device = get_model()
    except Exception as e:
        print(f"Failed to load model (likely missing deps or CUDA error): {e}")
        # If GPU required but failed, we re-raise to trigger offload mechanism
        if device == "cuda":
            raise RuntimeError("GPU required but unavailable. Please ensure CUDA environment.")
        raise e

    # 3. Inference & Evaluation
    results = []
    
    print(f"Running inference on {len(records)} records...")
    for i, record in enumerate(records):
        audio_path = resolve_audio_path(record)
        
        # Skip if audio missing (shouldn't happen in valid repo)
        if not os.path.exists(audio_path):
            print(f"Warning: Audio not found for record {i}, skipping.")
            continue
            
        # Transcribe
        prediction = transcribe_audio(audio_path, processor, model, device)
        reference = record.get("answer", "")
        
        # Determine Category
        category = public_category(record)
        if not category:
            category = "unknown"
            
        # Compute Metrics
        lang = detect_language(record)
        if lang == "zh":
            errors, ref_len = cer(reference, prediction)
            metric_type = "CER"
        else:
            errors, ref_len = wer(reference, prediction)
            metric_type = "WER"
            
        error_rate = (errors / ref_len * 100) if ref_len > 0 else 0.0
        
        results.append({
            "record_id": i,
            "category": category,
            "subset": record.get("subset", "unknown"),
            "language": lang,
            "reference": reference,
            "prediction": prediction,
            "errors": errors,
            "ref_len": ref_len,
            "error_rate": error_rate,
            "metric_type": metric_type
        })
        
        if (i + 1) % 5 == 0:
            print(f"  Processed {i+1}/{len(records)}")

    # 4. Save Results
    df = pd.DataFrame(results)
    csv_path = OUTPUT_DIR / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved detailed results to {csv_path}")
    
    # 5. Aggregate by Category
    summary = {}
    for cat in df["category"].unique():
        cat_df = df[df["category"] == cat]
        # Filter out unknowns for summary
        if cat == "unknown":
            continue
            
        total_errors = cat_df["errors"].sum()
        total_ref = cat_df["ref_len"].sum()
        avg_rate = (total_errors / total_ref * 100) if total_ref > 0 else 0.0
        
        summary[cat] = {
            "count": len(cat_df),
            "total_errors": int(total_errors),
            "total_ref_tokens": int(total_ref),
            "average_error_rate": round(avg_rate, 2),
            "metric": cat_df.iloc[0]["metric_type"]
        }
    
    summary_path = OUTPUT_DIR / "benchmark_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {summary_path}")
    
    # 6. Plot Results
    if summary:
        categories = list(summary.keys())
        rates = [summary[c]["average_error_rate"] for c in categories]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, rates, color='skyblue', edgecolor='navy')
        plt.title(f"ASR Error Rates by Acoustic Condition (Sample Size: {len(records)})")
        plt.ylabel("Error Rate (%)")
        plt.xlabel("Acoustic Category")
        plt.xticks(rotation=45)
        plt.ylim(0, max(rates) * 1.2 if rates else 10)
        
        # Add value labels on bars
        for bar, rate in zip(bars, rates):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                     f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
            
        plt.tight_layout()
        fig_path = FIGURES_DIR / "wer_by_category.png"
        plt.savefig(fig_path, dpi=150)
        print(f"Saved plot to {fig_path}")
    
    print("Benchmark complete.")

if __name__ == "__main__":
    run_benchmark()
