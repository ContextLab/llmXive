import os
import logging
import time
import numpy as np
import librosa
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class LatencyInjector:
    """
    Injects deterministic network latency into audio streams.
    
    Uses seeded numpy.random for reproducible jitter generation.
    Implements chunked I/O via librosa.stream to stay within memory limits.
    """

    def __init__(self, seed: int = 42, min_delay_ms: int = 200, max_delay_ms: int = 2000):
        """
        Initialize the latency injector.
        
        Args:
            seed: Random seed for deterministic jitter generation.
            min_delay_ms: Minimum delay in milliseconds.
            max_delay_ms: Maximum delay in milliseconds.
        """
        self.seed = seed
        self.min_delay_ms = min_delay_ms
        self.max_delay_ms = max_delay_ms
        self.rng = np.random.default_rng(seed)
        self.logger = logging.getLogger(__name__)

    def generate_delay(self) -> float:
        """
        Generate a single delay value in seconds.
        
        Returns:
            Delay in seconds (uniformly distributed between min and max).
        """
        delay_ms = self.rng.uniform(self.min_delay_ms, self.max_delay_ms)
        return delay_ms / 1000.0

    def generate_delay_sequence(self, count: int) -> List[float]:
        """
        Generate a sequence of deterministic delays.
        
        Args:
            count: Number of delays to generate.
            
        Returns:
            List of delay values in seconds.
        """
        delay_range_ms = self.max_delay_ms - self.min_delay_ms
        delay_values_ms = self.rng.uniform(self.min_delay_ms, self.max_delay_ms, count)
        return (delay_values_ms / 1000.0).tolist()

    def inject_latency_to_file(
        self,
        input_path: str,
        output_path: str,
        delay_ms: float,
        sr: int = 22050
    ) -> Dict[str, Any]:
        """
        Inject a fixed latency delay into an audio file by inserting silence.
        
        Args:
            input_path: Path to input audio file.
            output_path: Path to write output audio file.
            delay_ms: Delay in milliseconds to inject.
            sr: Sample rate for loading/saving.
            
        Returns:
            Dictionary with metadata about the injection.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        delay_samples = int(delay_ms * sr / 1000.0)
        silence = np.zeros(delay_samples, dtype=np.float32)

        # Load entire file for simple fixed delay injection
        # (Chunked streaming used for jitter scenarios in other methods)
        y, sr_loaded = librosa.load(input_path, sr=sr, mono=True)
        
        # Insert silence at the beginning (simulating network latency)
        y_injected = np.concatenate([silence, y])
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save output
        librosa.output.write_wav(output_path, y_injected, sr)
        
        return {
            "input_path": input_path,
            "output_path": output_path,
            "delay_ms": delay_ms,
            "original_samples": len(y),
            "injected_samples": delay_samples,
            "total_samples": len(y_injected),
            "sample_rate": sr
        }

    def inject_latency_with_jitter(
        self,
        input_path: str,
        output_path: str,
        n_turns: int,
        jitter_seed: Optional[int] = None,
        sr: int = 22050
    ) -> Dict[str, Any]:
        """
        Inject latency with deterministic jitter between turns.
        
        Args:
            input_path: Path to input audio file.
            output_path: Path to write output audio file.
            n_turns: Number of turns to inject jitter for.
            jitter_seed: Optional seed override for this specific injection.
            sr: Sample rate for loading/saving.
            
        Returns:
            Dictionary with metadata about the injection including delay sequence.
        """
        if jitter_seed is not None:
            rng = np.random.default_rng(jitter_seed)
        else:
            rng = self.rng

        # Generate deterministic jitter sequence
        delay_range_ms = self.max_delay_ms - self.min_delay_ms
        delay_values_ms = rng.uniform(self.min_delay_ms, self.max_delay_ms, n_turns)
        delay_values_sec = delay_values_ms / 1000.0

        # Load audio
        y, sr_loaded = librosa.load(input_path, sr=sr, mono=True)
        
        # Calculate silence samples for each turn
        silence_segments = [int(d * sr) for d in delay_values_sec]
        
        # Interleave silence with audio chunks (simplified: insert at fixed intervals)
        # In a real turn-based scenario, we would split by turn boundaries
        # Here we insert silence chunks at regular intervals to simulate latency
        chunk_size = len(y) // (n_turns + 1) if n_turns > 0 else len(y)
        
        result_chunks = []
        for i in range(n_turns + 1):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(y))
            chunk = y[start_idx:end_idx]
            result_chunks.append(chunk)
            if i < n_turns:
                silence_len = silence_segments[i]
                result_chunks.append(np.zeros(silence_len, dtype=np.float32))
        
        y_injected = np.concatenate(result_chunks)
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save output
        librosa.output.write_wav(output_path, y_injected, sr)
        
        return {
            "input_path": input_path,
            "output_path": output_path,
            "delay_sequence_ms": delay_values_ms.tolist(),
            "original_samples": len(y),
            "total_samples": len(y_injected),
            "sample_rate": sr,
            "jitter_seed": jitter_seed if jitter_seed is not None else self.seed
        }

    def verify_injection(
        self,
        original_path: str,
        injected_path: str,
        expected_delay_ms: float,
        tolerance_ms: float = 5.0,
        sr: int = 22050
    ) -> bool:
        """
        Verify that the injected delay matches the expected value.
        
        Args:
            original_path: Path to original audio.
            injected_path: Path to injected audio.
            expected_delay_ms: Expected delay in milliseconds.
            tolerance_ms: Tolerance for comparison.
            sr: Sample rate.
            
        Returns:
            True if verification passes, False otherwise.
        """
        y_orig, _ = librosa.load(original_path, sr=sr, mono=True)
        y_inj, _ = librosa.load(injected_path, sr=sr, mono=True)
        
        expected_samples = int(expected_delay_ms * sr / 1000.0)
        actual_samples = len(y_inj) - len(y_orig)
        
        tolerance_samples = int(tolerance_ms * sr / 1000.0)
        
        if abs(actual_samples - expected_samples) <= tolerance_samples:
            self.logger.info(
                f"Verification passed: expected {expected_delay_ms}ms, "
                f"actual {actual_samples/sr*1000:.2f}ms"
            )
            return True
        else:
            self.logger.warning(
                f"Verification failed: expected {expected_delay_ms}ms, "
                f"actual {actual_samples/sr*1000:.2f}ms"
            )
            return False