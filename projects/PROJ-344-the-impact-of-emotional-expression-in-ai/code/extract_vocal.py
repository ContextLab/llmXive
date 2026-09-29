"""
Vocal Prosody Extraction Module.

Extracts pitch, energy (RMS), and tempo features from audio tracks using librosa.
Aggregates these features per interaction and appends them to the master features CSV.
"""
import os
import glob
import numpy as np
import pandas as pd
import librosa
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import project utilities
from logging_config import get_logger, log_state_event
from utils import handle_corrupted_file
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

logger = get_logger(__name__)

# Constants
SAMPLING_RATE = 22050
HOP_LENGTH = 512
N_FFT = 2048
TEMPORAL_WINDOW_SEC = 1.0  # Window size for averaging features

def extract_pitch_features(y: np.ndarray, sr: int) -> Dict[str, float]:
    """
    Extract pitch-related features (mean, std, range) from the audio signal.
    Uses librosa's yin algorithm for robust pitch estimation.
    """
    try:
        # Estimate fundamental frequency
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
            frame_length=N_FFT,
            hop_length=HOP_LENGTH
        )

        # Filter out unvoiced frames (NaNs)
        f0_voiced = f0[~np.isnan(f0)]

        if len(f0_voiced) == 0:
            return {
                'pitch_mean': 0.0,
                'pitch_std': 0.0,
                'pitch_range': 0.0,
                'voiced_ratio': 0.0
            }

        pitch_mean = float(np.mean(f0_voiced))
        pitch_std = float(np.std(fo_voiced))
        pitch_range = float(np.max(f0_voiced) - np.min(f0_voiced))
        voiced_ratio = float(np.sum(~np.isnan(f0)) / len(f0))

        return {
            'pitch_mean': pitch_mean,
            'pitch_std': pitch_std,
            'pitch_range': pitch_range,
            'voiced_ratio': voiced_ratio
        }
    except Exception as e:
        logger.warning(f"Pitch extraction failed: {e}")
        return {
            'pitch_mean': 0.0,
            'pitch_std': 0.0,
            'pitch_range': 0.0,
            'voiced_ratio': 0.0
        }

def extract_energy_features(y: np.ndarray, sr: int) -> Dict[str, float]:
    """
    Extract energy-related features (RMS) from the audio signal.
    """
    try:
        # Calculate RMS energy
        rms = librosa.feature.rms(y=y, frame_length=N_FFT, hop_length=HOP_LENGTH)[0]

        energy_mean = float(np.mean(rms))
        energy_std = float(np.std(rms))
        energy_max = float(np.max(rms))

        # Energy entropy (simplified as variance of log energy)
        # Avoid log(0)
        rms_safe = np.maximum(rms, 1e-10)
        energy_entropy = float(np.std(np.log(rms_safe)))

        return {
            'energy_mean': energy_mean,
            'energy_std': energy_std,
            'energy_max': energy_max,
            'energy_entropy': energy_entropy
        }
    except Exception as e:
        logger.warning(f"Energy extraction failed: {e}")
        return {
            'energy_mean': 0.0,
            'energy_std': 0.0,
            'energy_max': 0.0,
            'energy_entropy': 0.0
        }

def extract_tempo(y: np.ndarray, sr: int) -> Dict[str, float]:
    """
    Extract tempo (BPM) and onset strength features.
    """
    try:
        # Estimate tempo
        tempo, beats = librosa.beat.beat_track(
            y=y,
            sr=sr,
            hop_length=HOP_LENGTH
        )

        # Calculate onset strength for rhythm analysis
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)
        onset_mean = float(np.mean(onset_env))
        onset_std = float(np.std(onset_env))

        return {
            'tempo_bpm': float(tempo),
            'onset_mean': onset_mean,
            'onset_std': onset_std
        }
    except Exception as e:
        logger.warning(f"Tempo extraction failed: {e}")
        return {
            'tempo_bpm': 0.0,
            'onset_mean': 0.0,
            'onset_std': 0.0
        }

def process_audio_file(audio_path: str, interaction_id: str) -> Optional[Dict[str, Any]]:
    """
    Process a single audio file and extract all vocal features.
    Returns a dictionary of features or None if the file is corrupted.
    """
    logger.info(f"Processing audio file: {audio_path}")

    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=SAMPLING_RATE, mono=True)

        if len(y) == 0:
            logger.warning(f"Empty audio file: {audio_path}")
            return None

        # Extract features
        pitch_features = extract_pitch_features(y, sr)
        energy_features = extract_energy_features(y, sr)
        tempo_features = extract_tempo(y, sr)

        # Combine features
        features = {
            'interaction_id': interaction_id,
            'duration_sec': float(len(y) / sr),
            **pitch_features,
            **energy_features,
            **tempo_features
        }

        return features

    except Exception as e:
        # Use project's error handling utility
        result = handle_corrupted_file(audio_path, e, logger)
        if result is None:
            logger.error(f"Failed to process {audio_path}: {e}")
        return None

def extract_vocal_prosody(input_dir: str, output_path: str) -> List[Dict[str, Any]]:
    """
    Scan input directory for audio files, extract vocal prosody,
    and save results to the output CSV.
    """
    logger.info(f"Starting vocal prosody extraction from {input_dir}")
    
    if not os.path.exists(input_dir):
        logger.warning(f"Input directory {input_dir} does not exist. Skipping extraction.")
        return []

    # Find all audio files (mp3, wav, flac, ogg)
    audio_extensions = ['*.mp3', '*.wav', '*.flac', '*.ogg', '*.m4a']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(glob.glob(os.path.join(input_dir, ext)))
        audio_files.extend(glob.glob(os.path.join(input_dir, '**', ext), recursive=True))

    if not audio_files:
        logger.warning(f"No audio files found in {input_dir}")
        return []

    logger.info(f"Found {len(audio_files)} audio files to process")

    all_features = []
    processed_count = 0
    failed_count = 0

    for audio_path in audio_files:
        # Derive interaction ID from filename (remove extension)
        interaction_id = Path(audio_path).stem

        features = process_audio_file(audio_path, interaction_id)
        
        if features:
            all_features.append(features)
            processed_count += 1
        else:
            failed_count += 1

    logger.info(f"Vocal extraction complete. Processed: {processed_count}, Failed: {failed_count}")

    # Save to CSV
    if all_features:
        df = pd.DataFrame(all_features)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Append to existing features.csv if it exists, otherwise create new
        if os.path.exists(output_path):
            existing_df = pd.read_csv(output_path)
            # Merge vocal features with existing facial features if they share interaction_id
            # For now, we assume we are appending columns or creating a new row structure.
            # Given the task description, we append rows to the master features file.
            # If interaction_id exists in existing, we might need to merge, 
            # but typically in this pipeline, we aggregate modalities per interaction.
            # Strategy: Concatenate vertically, assuming unique interaction IDs per row 
            # or that the downstream compute_metrics handles modalities.
            # However, usually facial and vocal are merged by interaction_id.
            # Let's assume the schema expects one row per interaction with combined features.
            # If existing_df has 'interaction_id', we should merge on it.
            
            if 'interaction_id' in existing_df.columns and 'interaction_id' in df.columns:
                # Merge on interaction_id
                merged_df = pd.merge(existing_df, df, on='interaction_id', how='outer')
                merged_df.to_csv(output_path, index=False)
                logger.info(f"Merged vocal features with existing features at {output_path}")
            else:
                # Fallback: append
                pd.concat([existing_df, df], ignore_index=True).to_csv(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)
            logger.info(f"Created new features file at {output_path}")
    
    log_state_event("Vocal Prosody Extraction Complete", {"processed": processed_count, "failed": failed_count})
    
    return all_features

def main():
    """
    Main entry point for the vocal prosody extraction script.
    """
    input_dir = DATA_RAW_DIR
    output_path = os.path.join(DATA_PROCESSED_DIR, "features.csv")
    
    # Ensure directories exist
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    extract_vocal_prosody(input_dir, output_path)
    logger.info("Vocal prosody extraction finished.")

if __name__ == "__main__":
    main()
