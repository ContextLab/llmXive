"""
Embedding Extraction Module for LlmXive Pipeline.

This module implements the extraction of fixed-dimensional latent embeddings
from audio samples using a frozen, lightweight encoder (distil-whisper-base).
It operates strictly in CPU-only mode and processes data in batches to manage
memory constraints.

Output:
    data/embeddings.parquet: A Parquet file containing columns:
        - 'audio_path': Path to the source audio file
        - 'label': String label ('jailbreak' or 'benign')
        - 'embedding': List[float] or fixed-size vector representation
        - 'duration': Audio duration in seconds
"""

import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import librosa
import torch
from transformers import WhisperProcessor, WhisperModel
from datasets import Dataset

# Import project utilities to match API surface
from src.utils.config import set_random_seed, get_path, ensure_dir, load_state
from src.utils.env_config import enforce_cpu_only, is_cpu_only_mode
from src.utils.logging_config import get_module_logger

# Ensure CPU-only execution immediately
enforce_cpu_only()

# Constants
BATCH_SIZE = 32
MODEL_NAME = "distil-whisper-base"
SAMPLE_RATE = 16000
MAX_DURATION_SECONDS = 30.0  # Truncate long audio to prevent OOM
EMBEDDING_DIM = 768  # Whisper base hidden size

logger = get_module_logger(__name__)


def load_model_and_processor() -> Tuple[WhisperModel, WhisperProcessor]:
    """
    Loads the frozen Distil-Whisper base model and processor for CPU inference.

    Returns:
        Tuple[WhisperModel, WhisperProcessor]: The loaded model and processor.
    """
    logger.info(f"Loading model: {MODEL_NAME} (CPU-only)")
    try:
        processor = WhisperProcessor.from_pretrained(MODEL_NAME, torch_dtype=torch.float32)
        model = WhisperModel.from_pretrained(MODEL_NAME, torch_dtype=torch.float32)
        
        # Freeze parameters
        model.eval()
        for param in model.parameters():
            param.requires_grad = False
        
        logger.info("Model loaded successfully and frozen.")
        return model, processor
    except Exception as e:
        logger.error(f"Failed to load model {MODEL_NAME}: {e}")
        raise


def load_audio_file(file_path: str) -> np.ndarray:
    """
    Loads an audio file using librosa, resampling to 16kHz.
    
    Args:
        file_path: Path to the audio file.
        
    Returns:
        np.ndarray: Audio waveform as a 1D numpy array.
        
    Raises:
        ValueError: If the file cannot be loaded or is invalid.
    """
    try:
        # Load with librosa, resample to 16kHz
        y, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
        
        # Truncate if too long to prevent memory issues
        if len(y) > SAMPLE_RATE * MAX_DURATION_SECONDS:
            y = y[: int(SAMPLE_RATE * MAX_DURATION_SECONDS)]
            
        return y
    except Exception as e:
        logger.error(f"Error loading audio file {file_path}: {e}")
        raise ValueError(f"Failed to load audio file: {file_path}") from e


def extract_embeddings_batch(
    model: WhisperModel, 
    processor: WhisperProcessor, 
    audio_batch: List[np.ndarray], 
    device: str
) -> List[np.ndarray]:
    """
    Extracts embeddings from a batch of audio waveforms.
    
    Args:
        model: The Whisper model.
        processor: The Whisper processor.
        audio_batch: List of 1D audio arrays.
        device: Device string (e.g., 'cpu').
        
    Returns:
        List[np.ndarray]: List of embedding vectors.
    """
    # Process batch through the processor
    # WhisperProcessor expects input_features for encoder
    inputs = processor(
        audio_batch, 
        sampling_rate=SAMPLE_RATE, 
        return_tensors="pt", 
        padding=True
    ).to(device)
    
    with torch.no_grad():
        # Extract hidden states from the encoder
        # distil-whisper-base encoder output shape: (batch, seq_len, hidden_size)
        # We take the mean pooling over the sequence length for a fixed vector
        outputs = model.encoder(**inputs)
        last_hidden_states = outputs.last_hidden_state  # (batch, seq_len, 768)
        
        # Mean pooling over sequence dimension
        # Masking is implicitly handled by padding in processor, but for simplicity
        # we take mean over non-padded if we had attention mask. 
        # Here, simple mean over seq_len is standard for fixed-dim rep.
        embeddings = last_hidden_states.mean(dim=1).cpu().numpy()
        
    return list(embeddings)


def process_dataset(
    data_dir: Path, 
    model: WhisperModel, 
    processor: WhisperProcessor,
    device: str
) -> pd.DataFrame:
    """
    Iterates through the dataset directory, loads audio, extracts embeddings,
    and builds a DataFrame.
    
    Args:
        data_dir: Path to the directory containing audio files and metadata.
        model: Loaded Whisper model.
        processor: Loaded Whisper processor.
        device: Device string.
        
    Returns:
        pd.DataFrame: DataFrame with embeddings and metadata.
    """
    # Assume data structure: data_dir contains subfolders or a manifest
    # Based on T012/T013 context, we expect a standard structure.
    # We will look for audio files and a manifest if available, 
    # or infer labels from directory structure if present.
    
    # Fallback: If specific manifest exists, use it. Otherwise, scan files.
    manifest_path = data_dir / "metadata.json"
    audio_files = []
    labels_map = {}
    
    if manifest_path.exists():
        logger.info(f"Loading manifest from {manifest_path}")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        for item in manifest:
            path = item.get('audio_path')
            label = item.get('label', 'unknown')
            if path:
                full_path = data_dir / path
                if full_path.exists():
                    audio_files.append(str(full_path))
                    labels_map[str(full_path)] = label
                else:
                    logger.warning(f"File in manifest not found: {full_path}")
    else:
        # Scan for audio files
        extensions = {'.wav', '.flac', '.mp3', '.ogg'}
        logger.info(f"Scanning {data_dir} for audio files...")
        for ext in extensions:
            for file_path in data_dir.rglob(f"*{ext}"):
                audio_files.append(str(file_path))
                # Infer label from directory name if possible, else 'unknown'
                parent_name = file_path.parent.name.lower()
                if 'jailbreak' in parent_name:
                    labels_map[str(file_path)] = 'jailbreak'
                elif 'benign' in parent_name:
                    labels_map[str(file_path)] = 'benign'
                else:
                    labels_map[str(file_path)] = 'unknown'
    
    if not audio_files:
        logger.warning("No audio files found to process.")
        return pd.DataFrame()

    logger.info(f"Processing {len(audio_files)} audio files in batches of {BATCH_SIZE}...")
    
    results = []
    start_time = time.time()
    processed_count = 0
    
    for i in range(0, len(audio_files), BATCH_SIZE):
        batch_paths = audio_files[i : i + BATCH_SIZE]
        batch_data = []
        batch_labels = []
        
        # Load audio for batch
        valid_indices = []
        for idx, path in enumerate(batch_paths):
            try:
                audio = load_audio_file(path)
                batch_data.append(audio)
                batch_labels.append(labels_map.get(path, 'unknown'))
                valid_indices.append(idx)
            except Exception as e:
                logger.warning(f"Skipping {path} due to error: {e}")
        
        if not batch_data:
            continue
            
        # Extract embeddings
        embeddings = extract_embeddings_batch(model, processor, batch_data, device)
        
        for idx, emb in enumerate(embeddings):
            orig_idx = valid_indices[idx]
            path = batch_paths[orig_idx]
            label = batch_labels[orig_idx]
            
            # Calculate duration roughly
            duration = len(batch_data[orig_idx]) / SAMPLE_RATE
            
            results.append({
                'audio_path': path,
                'label': label,
                'embedding': emb.tolist(),
                'duration': duration
            })
        
        processed_count += len(batch_data)
        elapsed = time.time() - start_time
        logger.info(f"Processed {processed_count}/{len(audio_files)} files ({elapsed:.1f}s)")

    return pd.DataFrame(results)


def main():
    """
    Main entry point for the embedding extraction pipeline.
    """
    # 1. Setup Environment
    set_random_seed(42)
    project_root = get_path("")
    data_dir = get_path("data")
    output_path = get_path("data/embeddings.parquet")
    
    ensure_dir(output_path.parent)
    
    logger.info("Starting Embedding Extraction Pipeline (T014)")
    logger.info(f"Project Root: {project_root}")
    logger.info(f"Input Data Dir: {data_dir}")
    logger.info(f"Output Path: {output_path}")
    
    # 2. Load Model
    model, processor = load_model_and_processor()
    device = "cpu" # Enforced by CPU-only config
    
    # 3. Process Dataset
    try:
        df = process_dataset(data_dir, model, processor, device)
        
        if df.empty:
            logger.error("No data processed. Exiting.")
            sys.exit(1)
            
        # 4. Save Results
        logger.info(f"Saving {len(df)} embeddings to {output_path}")
        df.to_parquet(output_path, index=False)
        
        # Validate output
        if output_path.exists():
            logger.info(f"Successfully wrote {output_path}")
            # Log schema info
            logger.info(f"Columns: {list(df.columns)}")
            logger.info(f"Embedding dim: {len(df['embedding'].iloc[0]) if 'embedding' in df.columns else 'N/A'}")
        else:
            logger.error("Output file was not created.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        logger.info("Embedding extraction finished.")


if __name__ == "__main__":
    main()
