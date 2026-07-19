from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib
import numpy as np

@dataclass
class AudioClip:
    """Represents a single audio clip with metadata."""
    clip_id: str
    speaker_id: str
    transcript: str
    audio_path: str
    snr_db: Optional[float] = None
    rt60: Optional[float] = None

@dataclass
class DistortionVector:
    """Represents a specific combination of distortion parameters."""
    vector_id: str
    snr_db: float
    rt60: float
    distortion_type: str = "compound"

@dataclass
class StressCurve:
    """Represents a stress curve for a specific clip and distortion scenario."""
    clip_id: str
    model_id: str
    scenario_id: str
    points: List[Dict[str, Any]] = field(default_factory=list)
    collapse_point: Optional[Dict[str, Any]] = None

def generate_interaction_terms(df: np.ndarray, feature_indices: List[int]) -> np.ndarray:
    """
    Generate interaction terms (SNR×RT60, SNR², RT60²) for regression features.

    Args:
        df: Input feature array (N x M)
        feature_indices: Indices of SNR and RT60 columns [snr_idx, rt60_idx]

    Returns:
        Extended feature array with interaction terms appended.
    """
    if len(feature_indices) != 2:
        raise ValueError("feature_indices must contain exactly 2 indices: [snr_idx, rt60_idx]")

    snr_idx, rt60_idx = feature_indices
    snr = df[:, snr_idx]
    rt60 = df[:, rt60_idx]

    interaction_snr_rt60 = snr * rt60
    snr_sq = snr ** 2
    rt60_sq = rt60 ** 2

    interaction_terms = np.column_stack([interaction_snr_rt60, snr_sq, rt60_sq])
    return np.hstack([df, interaction_terms])

def validate_hvcm_target(
    training_data_path: str,
    required_columns: List[str] = None
) -> bool:
    """
    Enforce FR-011: Assert that the regression target (HVCM) is derived from 
    human annotations and not from the SSS metric itself.

    This function reads the training data (typically a parquet or CSV containing 
    stress curve data merged with human annotations) and verifies the presence 
    of the `human_intelligibility_score` column. If this column is missing, 
    it raises a RuntimeError to prevent circularity where the model predicts 
    a metric derived from itself.

    Args:
        training_data_path: Path to the training data file (CSV or Parquet).
        required_columns: List of columns that must be present. Defaults to 
                          checking for 'human_intelligibility_score'.

    Raises:
        RuntimeError: If 'human_intelligibility_score' is missing from the data,
                      indicating a potential circularity violation.
        FileNotFoundError: If the training data file does not exist.
        ValueError: If the file format is unsupported or unreadable.
    """
    if required_columns is None:
        required_columns = ["human_intelligibility_score"]

    path = Path(training_data_path)
    if not path.exists():
        raise FileNotFoundError(f"Training data file not found: {training_data_path}")

    # Determine loader based on extension
    suffix = path.suffix.lower()
    try:
        if suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(path)
        elif suffix == '.parquet':
            import pandas as pd
            df = pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Expected .csv or .parquet.")
    except ImportError:
        raise RuntimeError("Pandas is required to validate training data. Install it via 'pip install pandas'.")

    # Check for the critical human annotation column
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        # Specifically check for the HVCM breaking condition
        if "human_intelligibility_score" in missing_cols:
            raise RuntimeError(
                f"CAUSALITY VIOLATION DETECTED: Training data at '{training_data_path}' "
                f"is missing the 'human_intelligibility_score' column. "
                f"Per FR-011, the HVCM target MUST be derived from human annotations. "
                f"Without this column, the model would predict SSS-based collapse points, "
                f"creating a circular dependency. Please ensure the training dataset includes "
                f"merged human validation data (see T030a)."
            )
        else:
            raise ValueError(f"Training data is missing required columns: {missing_cols}")

    logging.info(f"Validation passed: Training data contains human_intelligibility_score. "
                 f"Shape: {df.shape}, Columns: {list(df.columns)}")
    return True