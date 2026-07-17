"""
Distortion Engine for Mega-ASR Stress Curve Generation.

This module implements the generation of 54 distinct compound distortion vectors
based on SNR and RT60 parameter ranges, as required by FR-002.

It also provides the logic to apply these distortions to audio clips.
"""
import os
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
import json

# Ensure we can import from the project root if needed, though standard imports are preferred
# The API surface indicates `DistortionVector` is in `models.py`
try:
    from models import DistortionVector
except ImportError:
    # Fallback definition if models.py is not in path during standalone testing
    # This ensures the file is syntactically valid even in isolation
    @dataclass
    class DistortionVector:
        snr_db: float
        rt60_sec: float
        vector_id: int
        params: Dict[str, Any] = field(default_factory=dict)

logger = logging.getLogger(__name__)

# Constants for the 54 scenarios
# FR-002: 54 compound distortion scenarios (SNR x RT60)
# Based on typical acoustic stress testing ranges
SNR_LEVELS_DB = [-5, 0, 5, 10, 15, 20, 25]  # 7 levels
RT60_LEVELS_SEC = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]  # 6 levels
# 7 * 6 = 42? Wait, the task says 54.
# Let's re-evaluate standard ranges to hit 54 exactly.
# Maybe 9 SNR levels x 6 RT60 levels = 54?
# Or 6 SNR x 9 RT60?
# Let's assume a standard grid: SNR from -5 to 25 in steps of ~3.75? No, integers are better.
# Let's try: SNR: -10, -5, 0, 5, 10, 15, 20, 25, 30 (9 levels)
# RT60: 0.1, 0.3, 0.5, 0.7, 0.9, 1.1 (6 levels) -> 54.

# Adjusted parameters to strictly meet the 54 distinct vectors requirement
SNR_LEVELS_DB = [-10, -5, 0, 5, 10, 15, 20, 25, 30]  # 9 levels
RT60_LEVELS_SEC = [0.1, 0.3, 0.5, 0.7, 0.9, 1.1]  # 6 levels
# Total combinations: 9 * 6 = 54

@dataclass
class DistortionConfig:
    """Configuration for distortion generation."""
    snr_levels: List[float] = field(default_factory=lambda: SNR_LEVELS_DB)
    rt60_levels: List[float] = field(default_factory=lambda: RT60_LEVELS_SEC)
    sample_rate: int = 16000
    target_duration: float = 5.0  # Seconds for synthetic generation if needed

class DistortionEngine:
    """
    Engine to generate and apply compound acoustic distortions.
    
    Generates 54 distinct vectors mapping SNR and RT60 combinations.
    """
    
    def __init__(self, config: Optional[DistortionConfig] = None):
        self.config = config or DistortionConfig()
        self._vectors: List[DistortionVector] = []
        self._generate_vectors()
    
    def _generate_vectors(self) -> None:
        """
        Generates all 54 distinct distortion vectors based on configured SNR and RT60 levels.
        """
        self._vectors = []
        count = 0
        for snr in self.config.snr_levels:
            for rt60 in self.config.rt60_levels:
                count += 1
                vector = DistortionVector(
                    snr_db=snr,
                    rt60_sec=rt60,
                    vector_id=count,
                    params={
                        "snr_db": snr,
                        "rt60_sec": rt60,
                        "source": "grid_combination"
                    }
                )
                self._vectors.append(vector)
        
        if len(self._vectors) != 54:
            logger.warning(f"Expected 54 vectors, generated {len(self._vectors)}. Check SNR/RT60 level counts.")
            # We proceed anyway, but the test will catch the count mismatch.
        
        logger.info(f"Generated {len(self._vectors)} distortion vectors.")

    def get_vectors(self) -> List[DistortionVector]:
        """Returns the list of generated distortion vectors."""
        return self._vectors

    def apply_distortion(
        self, 
        audio_data: np.ndarray, 
        vector: DistortionVector, 
        sample_rate: int = 16000
    ) -> np.ndarray:
        """
        Applies a specific distortion vector to the input audio data.
        
        Args:
            audio_data: Raw audio samples (float32, -1.0 to 1.0).
            vector: The DistortionVector containing SNR and RT60 parameters.
            sample_rate: Audio sample rate in Hz.
        
        Returns:
            Distorted audio data.
        """
        if audio_data.ndim != 1:
            raise ValueError("Audio data must be 1D array.")
        
        # 1. Apply Reverberation (RT60)
        # Simulating RT60 with a simple decaying exponential impulse response
        # This is a lightweight approximation for the stress test pipeline.
        # A real implementation might use a full FIR filter or convolution with a RIR.
        decay_time = vector.rt60_sec
        if decay_time <= 0:
            rir = np.array([1.0])
        else:
            # Number of samples for the impulse response
            # We need enough length to cover the decay
            rir_length = int(4 * decay_time * sample_rate) 
            # Simple exponential decay: e^(-t / tau)
            # RT60 is time to decay by 60dB (factor of 1000).
            # e^(-T / tau) = 1/1000 => -T/tau = ln(1/1000) => tau = T / ln(1000)
            tau = decay_time / np.log(1000)
            t = np.arange(rir_length) / sample_rate
            rir = np.exp(-t / tau)
            rir = rir / np.sum(rir) # Normalize energy

        # Convolve audio with RIR
        # Use 'full' then trim or 'same'? 'same' keeps original length but loses tail.
        # For stress testing, we usually keep the full length or pad. 
        # Let's use 'same' to maintain array size for downstream processing, 
        # assuming the tail energy is negligible for the main segment.
        reverberated = np.convolve(audio_data, rir, mode='same')

        # 2. Apply Additive Noise (SNR)
        # Calculate current signal power
        signal_power = np.mean(reverberated ** 2)
        if signal_power < 1e-10:
            # Avoid division by zero for silent segments
            noise_power = 0
        else:
            # Target SNR in dB: 10 * log10(signal_power / noise_power)
            # noise_power = signal_power / 10^(SNR/10)
            snr_linear = 10 ** (vector.snr_db / 10.0)
            noise_power = signal_power / snr_linear
        
        # Generate white Gaussian noise
        noise = np.random.normal(0, np.sqrt(noise_power), size=reverberated.shape)
        
        # Add noise
        distorted_audio = reverberated + noise
        
        # Normalize to prevent clipping if necessary, though we preserve relative energy
        # Optional: Clip to [-1, 1]
        distorted_audio = np.clip(distorted_audio, -1.0, 1.0)
        
        return distorted_audio

def generate_all_distortion_vectors() -> List[DistortionVector]:
    """
    Convenience function to generate all 54 vectors using default configuration.
    
    Returns:
        List of DistortionVector objects.
    """
    engine = DistortionEngine()
    return engine.get_vectors()

def main():
    """
    Main entry point for the distortion engine.
    Generates vectors and prints summary.
    """
    logging.basicConfig(level=logging.INFO)
    engine = DistortionEngine()
    vectors = engine.get_vectors()
    
    print(f"Successfully generated {len(vectors)} distortion vectors.")
    print("First 5 vectors:")
    for v in vectors[:5]:
        print(f"  ID: {v.vector_id}, SNR: {v.snr_db}dB, RT60: {v.rt60_sec}s")
    print("...")
    print("Last 5 vectors:")
    for v in vectors[-5:]:
        print(f"  ID: {v.vector_id}, SNR: {v.snr_db}dB, RT60: {v.rt60_sec}s")
    
    return vectors

if __name__ == "__main__":
    main()
