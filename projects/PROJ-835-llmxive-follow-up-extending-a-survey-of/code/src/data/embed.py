import os
import sys
import json
import logging
import time
import traceback
import numpy as np
import pandas as pd
import torch
from transformers import WhisperProcessor, WhisperModel
from pathlib import Path
from typing import List, Dict, Any, Tuple
import soundfile as sf

# Local imports from project API surface
from src.utils.config import get_path, ensure_dir, get_artifact_hash
from src.utils.logging_config import get_module_logger
from src.utils.env_config import enforce_cpu_only

# Enforce CPU-only mode as per project constraints
enforce_cpu_only()

logger = get_module_logger(__name__)

# Expected embedding dimension for distil-whisper-base (768 for hidden states)
# distil-whisper-base uses a Whisper architecture with hidden_size=768
EXPECTED_EMBEDDING_DIM = 768

def load_model_and_processor(model_name: str = "distil-whisper-base") -> Tuple[Any, Any]:
    """
    Load the Whisper model and processor for CPU-only embedding extraction.
    
    Args:
        model_name: Name of the model to load (default: distil-whisper-base)
    
    Returns:
        Tuple of (processor, model)
    """
    logger.info(f"Loading model: {model_name}")
    
    try:
        processor = WhisperProcessor.from_pretrained(model_name)
        model = WhisperModel.from_pretrained(model_name)
        model.eval()  # Set to evaluation mode
        
        # Ensure model is on CPU
        model.to('cpu')
        
        logger.info(f"Model loaded successfully: {model_name}")
        return processor, model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def extract_embeddings_batch(
    audio_batch: List[np.ndarray],
    processor: Any,
    model: Any,
    batch_size: int = 32
) -> np.ndarray:
    """
    Extract embeddings from a batch of audio arrays.
    
    Args:
        audio_batch: List of numpy arrays containing audio data
        processor: Whisper processor
        model: Whisper model
        batch_size: Batch size for processing (default: 32)
    
    Returns:
        numpy array of shape (len(audio_batch), EXPECTED_EMBEDDING_DIM)
    """
    embeddings = []
    
    for i in range(0, len(audio_batch), batch_size):
        batch = audio_batch[i:i + batch_size]
        
        # Process audio batch
        inputs = processor(
            batch,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )
        
        # Move inputs to CPU
        input_features = inputs.input_features.to('cpu')
        
        with torch.no_grad():
            # Extract hidden states from the last layer
            outputs = model(input_features, output_hidden_states=True)
            
            # Get the last hidden state (shape: batch_size, seq_len, hidden_size)
            last_hidden_state = outputs.hidden_states[-1]
            
            # Take the mean across the sequence dimension to get fixed-size embedding
            # Shape: (batch_size, hidden_size)
            batch_embeddings = last_hidden_state.mean(dim=1).cpu().numpy()
            
            # Validate dimensionality BEFORE appending
            for j, emb in enumerate(batch_embeddings):
                actual_dim = emb.shape[0]
                if actual_dim != EXPECTED_EMBEDDING_DIM:
                    raise ValueError(
                        f"Dimensionality mismatch: expected {EXPECTED_EMBEDDING_DIM}, "
                        f"got {actual_dim} for sample {i + j}"
                    )
            
            embeddings.append(batch_embeddings)
    
    return np.vstack(embeddings)

def load_audio_file(file_path: str) -> np.ndarray:
    """
    Load an audio file and return as numpy array.
    
    Args:
        file_path: Path to the audio file
    
    Returns:
        numpy array of audio data
    """
    try:
        audio_data, sample_rate = sf.read(file_path)
        
        # Resample to 16kHz if necessary (Whisper expects 16kHz)
        if sample_rate != 16000:
            from scipy import signal
            audio_data = signal.resample(audio_data, int(len(audio_data) * 16000 / sample_rate))
        
        return audio_data
    except Exception as e:
        logger.error(f"Failed to load audio file {file_path}: {e}")
        raise

def process_dataset(
    audio_files: List[str],
    labels: List[str],
    processor: Any,
    model: Any,
    output_path: str,
    batch_size: int = 32
) -> str:
    """
    Process a dataset of audio files and extract embeddings.
    
    Args:
        audio_files: List of paths to audio files
        labels: List of corresponding labels (e.g., 'benign', 'jailbreak')
        processor: Whisper processor
        model: Whisper model
        output_path: Path to save the embeddings parquet file
        batch_size: Batch size for processing
    
    Returns:
        Path to the saved embeddings file
    """
    logger.info(f"Processing {len(audio_files)} audio files")
    
    all_embeddings = []
    all_labels = []
    all_file_paths = []
    
    for i, (audio_path, label) in enumerate(zip(audio_files, labels)):
        try:
            audio_data = load_audio_file(audio_path)
            all_embeddings.append(audio_data)
            all_labels.append(label)
            all_file_paths.append(audio_path)
            
            # Process in batches
            if len(all_embeddings) >= batch_size:
                batch_embeddings = extract_embeddings_batch(
                    all_embeddings, processor, model, batch_size=batch_size
                )
                for j, emb in enumerate(batch_embeddings):
                    # Store as list for pandas compatibility
                    pass  # We'll handle this differently below
                
                # Reset batch
                all_embeddings = []
                
        except Exception as e:
            logger.warning(f"Skipping file {audio_path}: {e}")
            continue
    
    # Process remaining items
    if all_embeddings:
        batch_embeddings = extract_embeddings_batch(
            all_embeddings, processor, model, batch_size=batch_size
        )
    else:
        batch_embeddings = np.array([])
    
    # Combine all embeddings (this is a simplification; in practice, we'd accumulate properly)
    # For the actual implementation, we need to restructure to accumulate properly
    
    # Let's restructure for proper batch accumulation
    all_embeddings = []
    all_labels = []
    all_file_paths = []
    
    for i, (audio_path, label) in enumerate(zip(audio_files, labels)):
        try:
            audio_data = load_audio_file(audio_path)
            all_embeddings.append(audio_data)
            all_labels.append(label)
            all_file_paths.append(audio_path)
            
            # Process in batches
            if len(all_embeddings) >= batch_size:
                batch_embeddings = extract_embeddings_batch(
                    all_embeddings, processor, model, batch_size=batch_size
                )
                all_embeddings = []  # Reset for next batch
                
                # Save batch results temporarily
                # In a real implementation, we'd accumulate these
        except Exception as e:
            logger.warning(f"Skipping file {audio_path}: {e}")
            continue
    
    # Final batch
    if all_embeddings:
        batch_embeddings = extract_embeddings_batch(
            all_embeddings, processor, model, batch_size=len(all_embeddings)
        )
    else:
        batch_embeddings = np.array([])
    
    # For the actual implementation, we need to properly accumulate embeddings
    # Let's implement a cleaner version that accumulates properly
    
    # Reset and do it properly
    all_embeddings = []
    all_labels = []
    all_file_paths = []
    processed_count = 0
    
    # Group into batches first
    batches = []
    current_batch_files = []
    current_batch_labels = []
    
    for audio_path, label in zip(audio_files, labels):
        current_batch_files.append(audio_path)
        current_batch_labels.append(label)
        
        if len(current_batch_files) >= batch_size:
            batches.append((current_batch_files, current_batch_labels))
            current_batch_files = []
            current_batch_labels = []
    
    # Add remaining
    if current_batch_files:
        batches.append((current_batch_files, current_batch_labels))
    
    # Process each batch
    for batch_files, batch_labels in batches:
        batch_audio_data = []
        for audio_path in batch_files:
            try:
                audio_data = load_audio_file(audio_path)
                batch_audio_data.append(audio_data)
            except Exception as e:
                logger.warning(f"Skipping file {audio_path}: {e}")
                continue
        
        if not batch_audio_data:
            continue
        
        try:
            batch_embeddings = extract_embeddings_batch(
                batch_audio_data, processor, model, batch_size=batch_size
            )
            
            for emb, label, file_path in zip(batch_embeddings, batch_labels, batch_files):
                all_embeddings.append(emb.tolist())
                all_labels.append(label)
                all_file_paths.append(file_path)
                processed_count += 1
                
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            continue
    
    logger.info(f"Successfully processed {processed_count} files")
    
    # Create DataFrame
    df = pd.DataFrame({
        'file_path': all_file_paths,
        'label': all_labels,
        'embedding': all_embeddings
    })
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    ensure_dir(output_dir)
    
    # Save to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved embeddings to {output_path}")
    
    return output_path

def main():
    """Main entry point for embedding extraction."""
    logger.info("Starting embedding extraction pipeline")
    
    # Example usage - in practice, this would be driven by CLI or config
    # For now, we'll demonstrate the dimensionality validation logic
    
    # Load model
    processor, model = load_model_and_processor("distil-whisper-base")
    
    # Create sample data for testing dimensionality validation
    # In a real scenario, this would come from a dataset
    sample_audio = np.random.randn(16000)  # 1 second of random audio at 16kHz
    
    try:
        # Extract embedding from single sample
        batch_embedding = extract_embeddings_batch(
            [sample_audio], processor, model, batch_size=1
        )
        
        # Validate dimensionality
        if batch_embedding.shape[1] != EXPECTED_EMBEDDING_DIM:
            raise ValueError(
                f"Dimensionality validation failed: expected {EXPECTED_EMBEDDING_DIM}, "
                f"got {batch_embedding.shape[1]}"
            )
        
        logger.info(f"Dimensionality validation passed: {batch_embedding.shape[1]} dimensions")
        
    except Exception as e:
        logger.error(f"Embedding extraction failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("Embedding extraction pipeline completed successfully")

if __name__ == "__main__":
    main()