from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib
import numpy as np

@dataclass
class AudioClip:
    """Represents an audio clip with metadata."""
    path: str
    text: str
    speaker_id: str
    accent: str
    duration: float = 0.0

@dataclass
class DistortionVector:
    """Represents a distortion vector."""
    snr: float
    rt60: float
    vector_id: str

@dataclass
class StressCurve:
    """Represents a stress curve data point."""
    clip_id: str
    vector_id: str
    snr: float
    rt60: float
    sss: float
    wer: float

def generate_interaction_terms(features: np.ndarray) -> np.ndarray:
    """
    Generate interaction terms for regression.
    Adds SNR×RT60, SNR², RT60² to the feature set.
    """
    snr = features[:, 0]
    rt60 = features[:, 1]
    
    interaction_snr_rt60 = snr * rt60
    snr_squared = snr ** 2
    rt60_squared = rt60 ** 2
    
    # Stack original features with interaction terms
    interaction_terms = np.column_stack([
        interaction_snr_rt60,
        snr_squared,
        rt60_squared
    ])
    
    return np.hstack([features, interaction_terms])

def validate_hvcm_target(data: List[Dict[str, Any]]) -> bool:
    """
    Validate that HVCM target is derived from human annotations.
    Raises error if human_intelligibility_score is missing.
    """
    if not data:
        return False
    
    if "human_intelligibility_score" not in data[0]:
        raise ValueError("Human intelligibility score is missing from data. HVCM target cannot be validated.")
    
    return True

def main():
    """Main entry point for models testing."""
    print("Models module loaded successfully")

if __name__ == "__main__":
    main()