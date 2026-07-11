"""
Latency Injection Module for EVA-Bench Extension.

Implements the LatencyInjector class to inject variable network latency
into audio streams using chunked I/O (librosa.stream) to stay within
memory constraints.
"""
import os
import logging
import time
import numpy as np
import librosa
from pathlib import Path
from typing import Optional, List, Tuple

from ..logging_config import setup_logging

# Initialize logger for this module
logger = setup_logging("LatencyInjector", "code/logs/latency_injection.log")


class LatencyInjector:
    """
    Injects synthetic network latency into audio streams.

    This class processes audio in chunks to handle large files within
    memory limits, inserting silence gaps to simulate latency.

    Attributes:
        target_latency_ms (float): Target latency in milliseconds to inject.
        jitter_range_ms (float): Range for random jitter (± value).
        sample_rate (int): Target sample rate for output (default 22050).
        chunk_duration_sec (float): Duration of audio chunks for streaming.
    """

    def __init__(
        self,
        target_latency_ms: float = 500.0,
        jitter_range_ms: float = 0.0,
        sample_rate: int = 22050,
        chunk_duration_sec: float = 1.0,
        seed: Optional[int] = None
    ):
        """
        Initialize the LatencyInjector.

        Args:
            target_latency_ms: Base latency to inject in milliseconds.
            jitter_range_ms: Symmetric jitter range in milliseconds.
            sample_rate: Output sample rate.
            chunk_duration_sec: Duration of chunks for streaming I/O.
            seed: Random seed for deterministic jitter.
        """
        self.target_latency_ms = target_latency_ms
        self.jitter_range_ms = jitter_range_ms
        self.sample_rate = sample_rate
        self.chunk_duration_sec = chunk_duration_sec
        
        if seed is not None:
            np.random.seed(seed)
            logger.info(f"Random seed set to {seed}")
        
        logger.info(f"LatencyInjector initialized: target={target_latency_ms}ms, jitter=±{jitter_range_ms}ms")

    def _calculate_gap_samples(self) -> int:
        """
        Calculate the number of silence samples to insert based on current latency settings.
        
        Returns:
            int: Number of zero samples representing the latency gap.
        """
        total_latency_ms = self.target_latency_ms
        
        if self.jitter_range_ms > 0:
            # Apply jitter if configured
            jitter = np.random.uniform(-self.jitter_range_ms, self.jitter_range_ms)
            total_latency_ms += jitter
            logger.debug(f"Applied jitter: {jitter:.2f}ms -> total latency: {total_latency_ms:.2f}ms")
        
        # Convert ms to samples
        gap_samples = int((total_latency_ms / 1000.0) * self.sample_rate)
        return max(0, gap_samples)

    def inject_latency(
        self,
        input_path: str,
        output_path: str,
        gap_position: str = "start"
    ) -> Tuple[str, float, float]:
        """
        Inject latency into an audio file by inserting silence.

        Args:
            input_path: Path to the input audio file.
            output_path: Path where the perturbed audio will be saved.
            gap_position: Where to insert the gap. Options: "start", "end", "middle".
                          Default is "start".

        Returns:
            Tuple containing:
                - output_path (str): Path to the generated file.
                - original_duration (float): Duration of original audio in seconds.
                - new_duration (float): Duration of modified audio in seconds.
        
        Raises:
            FileNotFoundError: If input file does not exist.
            ValueError: If gap_position is invalid.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input audio file not found: {input_path}")

        valid_positions = ["start", "end", "middle"]
        if gap_position not in valid_positions:
            raise ValueError(f"gap_position must be one of {valid_positions}")

        # Calculate gap size
        gap_samples = self._calculate_gap_samples()
        logger.info(f"Calculated gap size: {gap_samples} samples ({gap_samples / self.sample_rate:.3f}s)")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Process audio in chunks using librosa.stream
        original_duration = 0.0
        chunk_count = 0
        first_chunk = True
        
        # We will write to a temporary list of chunks first to manage the gap insertion logic
        # then write to file. For very large files, we could stream write directly,
        # but managing the gap position "middle" requires knowing the total length or 
        # buffering. Given typical EVA-Bench audio sizes (< 50MB), buffering chunks 
        # into a list is safe and simpler than complex seek logic on raw files.
        
        processed_chunks = []
        gap_inserted = False

        try:
            # Open stream
            # librosa.load returns (y, sr). stream returns an iterator of chunks.
            # We use librosa.stream to avoid loading full file into RAM.
            stream = librosa.stream(
                input_path,
                block_length=self.chunk_duration_sec * self.sample_rate,
                frame_length=2048,
                hop_length=512,
                mono=True
            )

            for chunk in stream:
                # chunk is a numpy array
                processed_chunks.append(chunk)
                original_duration += len(chunk) / self.sample_rate
                chunk_count += 1

                # Insert gap logic
                if not gap_inserted:
                    if gap_position == "start" and first_chunk:
                        logger.debug(f"Inserting gap at start before chunk {chunk_count}")
                        processed_chunks.insert(-1, np.zeros(gap_samples, dtype=chunk.dtype))
                        gap_inserted = True
                    
                    elif gap_position == "middle" and chunk_count == (chunk_count // 2 + 1):
                        # Insert after roughly half the chunks
                        logger.debug(f"Inserting gap at middle after chunk {chunk_count}")
                        processed_chunks.insert(-1, np.zeros(gap_samples, dtype=chunk.dtype))
                        gap_inserted = True
                
                first_chunk = False

            # If gap not inserted yet (e.g., empty file or specific logic edge), insert at end
            if not gap_inserted and gap_position == "end":
                logger.debug("Inserting gap at end")
                processed_chunks.append(np.zeros(gap_samples, dtype=processed_chunks[0].dtype if processed_chunks else np.float32))
            elif not gap_inserted and gap_position == "middle" and chunk_count > 0:
                # Fallback for small files where middle logic didn't trigger
                logger.warning("Gap insertion for 'middle' failed to trigger, inserting at end.")
                processed_chunks.append(np.zeros(gap_samples, dtype=processed_chunks[0].dtype))

        except Exception as e:
            logger.error(f"Error during streaming read of {input_path}: {e}")
            raise

        # Concatenate all chunks
        if not processed_chunks:
            logger.warning(f"No audio data found in {input_path}, writing empty file")
            final_audio = np.array([], dtype=np.float32)
        else:
            final_audio = np.concatenate(processed_chunks)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write output
        try:
            librosa.output.write_wav(output_path, final_audio, self.sample_rate)
        except AttributeError:
            # Fallback for newer librosa versions where write_wav might be removed or changed
            # In newer librosa, we might need to use soundfile directly or librosa.output.write
            try:
                import soundfile as sf
                sf.write(output_path, final_audio, self.sample_rate)
            except ImportError:
                raise RuntimeError("soundfile library not found. Cannot write WAV file.")

        new_duration = len(final_audio) / self.sample_rate
        logger.info(f"Successfully wrote {output_path}. Original: {original_duration:.3f}s, New: {new_duration:.3f}s")

        return output_path, original_duration, new_duration

    def inject_latency_to_file(
        self,
        input_path: str,
        output_path: str
    ) -> Tuple[str, float, float]:
        """
        Convenience method to inject latency at the start of the file.
        
        Args:
            input_path: Input audio file path.
            output_path: Output audio file path.
        
        Returns:
            Tuple of (output_path, original_duration, new_duration).
        """
        return self.inject_latency(input_path, output_path, gap_position="start")