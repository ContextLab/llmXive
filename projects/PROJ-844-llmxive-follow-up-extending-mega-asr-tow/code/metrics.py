import os
import sys
import json
import logging
import math
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
import pandas as pd

# Defensive CPU Enforcement: Check for CUDA/GPU immediately upon import
# This ensures the "Fail Loudly" principle is enforced before any heavy computation begins.
def _enforce_cpu_only():
    """
    Raises RuntimeError immediately if any CUDA device is detected or if GPU libraries
    are inadvertently configured for GPU usage.
    """
    # Check PyTorch if available
    try:
        import torch
        if torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is available. This project is strictly CPU-only to ensure reproducibility "
                "and avoid silent GPU fallbacks. Please set CUDA_VISIBLE_DEVICES='' or "
                "uninstall torch with CUDA support, or explicitly configure models to use CPU."
            )
        # Check if any GPU device is registered even if not currently available (rare edge case)
        if torch.cuda.device_count() > 0:
            raise RuntimeError(
                f"Detected {torch.cuda.device_count()} CUDA device(s). "
                "This pipeline enforces CPU-only execution. "
                "Set environment variable CUDA_VISIBLE_DEVICES='' to proceed."
            )
    except ImportError:
        pass  # Torch not installed, skip check

    # Check TensorFlow if available
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            raise RuntimeError(
                f"Detected {len(gpus)} GPU(s) via TensorFlow. "
                "This pipeline enforces CPU-only execution. "
                "Please configure TensorFlow to use CPU only or unset GPU visibility."
            )
    except ImportError:
        pass  # TensorFlow not installed, skip check

    # Check JAX if available
    try:
        import jax
        if jax.default_backend() != 'cpu':
            raise RuntimeError(
                f"JAX default backend is {jax.default_backend()}. "
                "This pipeline enforces CPU-only execution. "
                "Set JAX_PLATFORMS=cpu to proceed."
            )
    except ImportError:
        pass  # JAX not installed, skip check

    logging.info("CPU-only enforcement check passed. No GPU devices detected.")

# Run the check immediately when the module is imported
_enforce_cpu_only()

from sentence_transformers import SentenceTransformer
from transformers import WhisperProcessor, AutoModelForSpeechSeq2Seq
from jiwer import wer
import torch

from config import get_config
from models import AudioClip, DistortionVector, StressCurve

logger = logging.getLogger(__name__)

class MetricsCalculator:
    """
    Calculates Semantic Similarity Score (SSS) and Word Error Rate (WER)
    for audio clips under various distortion scenarios.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.device = "cpu"  # Enforced by _enforce_cpu_only() above
        
        # Initialize models
        logger.info("Initializing embedding model (all-MiniLM-L6-v2) on CPU...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
        
        logger.info("Initializing ASR model (whisper-tiny) on CPU...")
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
        self.asr_model = AutoModelForSpeechSeq2Seq.from_pretrained(
            "openai/whisper-tiny",
            torch_dtype=torch.float32,
            use_safetensors=True
        )
        self.asr_model.to(self.device)
        self.asr_model.eval()

    def compute_sss(self, reference_text: str, hypothesis_text: str) -> float:
        """
        Computes Semantic Similarity Score (SSS) using cosine similarity of embeddings.
        """
        if not reference_text or not hypothesis_text:
            return 0.0
        
        embeddings = self.embedding_model.encode([reference_text, hypothesis_text])
        sim = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
        # Normalize from [-1, 1] to [0, 1]
        return float((sim + 1) / 2)

    def compute_wer(self, reference_text: str, hypothesis_text: str) -> float:
        """
        Computes Word Error Rate (WER) using jiwer.
        """
        if not reference_text or not hypothesis_text:
            return 1.0
        
        return wer(reference_text, hypothesis_text)

    def transcribe_audio(self, audio_data: np.ndarray, sampling_rate: int) -> str:
        """
        Transcribes audio data using the ASR model.
        """
        inputs = self.processor(audio_data, sampling_rate=sampling_rate, return_tensors="pt")
        with torch.no_grad():
            generated_ids = self.asr_model.generate(
                inputs["input_features"],
                max_new_tokens=128,
                do_sample=False,
            )
        transcription = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return transcription

def compute_baseline_sss_and_wer(
    stress_curves_path: Path,
    models_list: List[str],
    output_dir: Path
) -> Tuple[Path, Path]:
    """
    Computes baseline SSS and WER for clean audio subsets.
    Outputs baseline_sss.json and baseline_wer.json.
    """
    df = pd.read_parquet(stress_curves_path)
    
    # Filter for clean audio (distortion_vector_id == 'clean' or similar indicator)
    # Assuming 'clean' is the identifier for no distortion
    clean_df = df[df['distortion_vector_id'].str.contains('clean', case=False, na=False)]
    
    if clean_df.empty:
        raise ValueError("No clean audio samples found in stress curves data.")
    
    baseline_sss = {}
    baseline_wer = {}
    
    calculator = MetricsCalculator()
    
    for model_id in models_list:
        model_df = clean_df[clean_df['model_id'] == model_id]
        if model_df.empty:
            logger.warning(f"No clean data for model {model_id}, skipping baseline calculation.")
            continue
        
        sss_scores = []
        wer_scores = []
        
        for _, row in model_df.iterrows():
            sss_scores.append(row['sss'])
            wer_scores.append(row['wer'])
        
        avg_sss = np.mean(sss_scores)
        avg_wer = np.mean(wer_scores)
        
        baseline_sss[model_id] = avg_sss
        baseline_wer[model_id] = avg_wer
        
        logger.info(f"Baseline for {model_id}: SSS={avg_sss:.4f}, WER={avg_wer:.4f}")
    
    baseline_sss_path = output_dir / "baseline_sss.json"
    baseline_wer_path = output_dir / "baseline_wer.json"
    
    with open(baseline_sss_path, 'w') as f:
        json.dump(baseline_sss, f, indent=2)
    with open(baseline_wer_path, 'w') as f:
        json.dump(baseline_wer, f, indent=2)
        
    return baseline_sss_path, baseline_wer_path

def compute_hvcm_target(
    stress_curves_path: Path,
    human_annotations_path: Path,
    collapse_points_path: Path,
    output_path: Path
) -> Path:
    """
    Computes Human-Validated Collapse Margin (HVCM) target.
    HVCM = SSS-based collapse point - human-annotated collapse point.
    """
    stress_curves = pd.read_parquet(stress_curves_path)
    human_annotations = pd.read_csv(human_annotations_path)
    collapse_points = pd.read_parquet(collapse_points_path)
    
    # Merge human annotations with stress curves to align data
    # Assuming 'clip_id' and 'distortion_vector_id' are common keys
    merged = pd.merge(
        stress_curves,
        human_annotations,
        on=['clip_id', 'distortion_vector_id'],
        how='inner'
    )
    
    if merged.empty:
        raise ValueError("No overlapping data between stress curves and human annotations.")
    
    # Group by clip_id and model_id to find collapse points
    # For human annotations, we need to determine the collapse point based on Likert scores
    # Assuming Likert scale 0-5, collapse might be defined as score < 3 (arbitrary, adjust based on spec)
    # For this implementation, we'll find the first distortion level where human score drops below threshold
    
    hvcm_data = []
    
    for (clip_id, model_id), group in merged.groupby(['clip_id', 'model_id']):
        # Sort by distortion intensity (assuming 'snr' or 'rt60' indicates intensity)
        # Here we use 'snr' as the intensity metric, lower SNR = higher distortion
        group = group.sort_values('snr')
        
        # Find SSS collapse point from stress curve data
        sss_collapse = None
        for idx, row in group.iterrows():
            if row['sss'] < 0.5:  # Threshold for SSS collapse
                sss_collapse = row['snr']
                break
        
        if sss_collapse is None:
            sss_collapse = group['snr'].max()  # Max tested if no collapse
        
        # Find human collapse point
        human_collapse = None
        for idx, row in group.iterrows():
            if row['human_intelligibility_score_0_5'] < 3:  # Threshold for human collapse
                human_collapse = row['snr']
                break
        
        if human_collapse is None:
            human_collapse = group['snr'].max()
        
        hvcm = sss_collapse - human_collapse
        
        hvcm_data.append({
            'clip_id': clip_id,
            'model_id': model_id,
            'sss_collapse_point': sss_collapse,
            'human_collapse_point': human_collapse,
            'hvcm': hvcm
        })
    
    hvcm_df = pd.DataFrame(hvcm_data)
    hvcm_df.to_parquet(output_path, index=False)
    logger.info(f"HVCM targets saved to {output_path}")
    
    return output_path

def main():
    """
    Main function to run metrics calculations.
    """
    config = get_config()
    output_dir = Path(config['data']['derived'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Example usage (to be replaced with actual CLI arguments in production)
    stress_curves_path = Path(config['data']['derived']) / "stress_curves.parquet"
    human_annotations_path = Path(config['data']['validation']) / "human_annotations.csv"
    collapse_points_path = Path(config['data']['derived']) / "collapse_points.parquet"
    
    if not stress_curves_path.exists():
        logger.error(f"Stress curves file not found: {stress_curves_path}")
        return
        
    if not human_annotations_path.exists():
        logger.error(f"Human annotations file not found: {human_annotations_path}")
        return
        
    if not collapse_points_path.exists():
        logger.error(f"Collapse points file not found: {collapse_points_path}")
        return
        
    # Compute HVCM target
    hvcm_output = output_dir / "hvcm_targets.parquet"
    compute_hvcm_target(stress_curves_path, human_annotations_path, collapse_points_path, hvcm_output)
    
    logger.info("Metrics calculation completed successfully.")

if __name__ == "__main__":
    main()
