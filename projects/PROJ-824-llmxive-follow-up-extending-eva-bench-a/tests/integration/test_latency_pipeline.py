"""
Integration test suite for LatencyInjector.

This module contains integration tests for:
1. Fixed delay scenarios (800ms).
2. Jitter variability scenarios (±50ms).

Prerequisites:
- T014 (LatencyInjector implementation) must be complete.
- A valid audio file must exist in data/raw/ or be generated via T007.
"""
import os
import sys
import tempfile
import shutil
import logging
import numpy as np
import librosa
from pathlib import Path
import pytest

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.injectors.latency import LatencyInjector
from code.config import ensure_directories
from code.logging_config import setup_logging
from code.synthetic.tts_engine import TTSEngine

# Configure logging for the test
logger = setup_logging("test_latency_integration", level=logging.INFO)

# Constants
FIXED_DELAY_MS = 800
JITTER_MS = 50
TOLERANCE_MS = 100  # Slightly higher tolerance for jitter variance
SAMPLE_RATE = 22050  # Standard for EVA-Bench/Coqui TTS

def _generate_test_audio(output_path: Path, duration_sec: float = 2.0) -> None:
    """
    Generate a deterministic test audio file using TTSEngine or synthetic noise
    if TTS is unavailable.
    
    Args:
        output_path: Path to write the .wav file.
        duration_sec: Duration of the audio in seconds.
    """
    # Attempt to use the real TTS engine defined in T007
    try:
        engine = TTSEngine(seed=42)
        text = "This is a test audio file for latency injection verification."
        engine.synthesize(text, output_path)
        logger.info(f"Generated test audio via TTS at {output_path}")
    except Exception as e:
        logger.warning(f"TTS generation failed ({e}), falling back to synthetic sine wave.")
        # Fallback: Generate a simple sine wave
        t = np.linspace(0, duration_sec, int(duration_sec * SAMPLE_RATE), endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz sine wave
        librosa.output.write_wav(str(output_path), audio, SAMPLE_RATE)
        logger.info(f"Generated synthetic test audio at {output_path}")

def _get_duration(file_path: Path) -> float:
    """Get duration of audio file in seconds."""
    y, sr = librosa.load(str(file_path), sr=None)
    return len(y) / sr

@pytest.fixture(scope="function")
def test_environment(tmp_path):
    """Set up temporary directories and test audio file."""
    # Create necessary directories
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Generate input audio
    input_audio = raw_dir / "test_input.wav"
    _generate_test_audio(input_audio, duration_sec=3.0)
    
    # Verify input exists
    assert input_audio.exists(), "Input audio generation failed"
    
    return {
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
        "input_audio": input_audio,
        "output_fixed": processed_dir / "test_output_fixed.wav",
        "output_jitter": processed_dir / "test_output_jitter.wav"
    }

def test_latency_injection_800ms_fixed_delay(test_environment):
    """
    Integration test: Verify that injecting 800ms fixed delay increases duration correctly.
    
    Steps:
    1. Load input audio.
    2. Run LatencyInjector with fixed_delay_ms=800.
    3. Measure output duration.
    4. Assert output_duration >= input_duration + (800ms - tolerance).
    """
    input_path = test_environment["input_audio"]
    output_path = test_environment["output_fixed"]
    
    # Record input duration
    input_duration = _get_duration(input_path)
    logger.info(f"Input audio duration: {input_duration:.3f}s")
    
    # Initialize the injector
    injector = LatencyInjector(
        fixed_delay_ms=FIXED_DELAY_MS,
        jitter_ms=0,
        turn_boundaries_path=None,
        logger=logger
    )
    
    # Run injection
    try:
        injector.process_file(str(input_path), str(output_path))
    except Exception as e:
        logger.error(f"Latency injection failed: {e}")
        pytest.fail(f"LatencyInjector.process_file raised an exception: {e}")
    
    # Verify output file exists
    assert output_path.exists(), "Output audio file was not created"
    
    # Measure output duration
    output_duration = _get_duration(output_path)
    logger.info(f"Output audio duration (fixed): {output_duration:.3f}s")
    
    # Calculate expected minimum duration
    expected_min_duration = input_duration + (FIXED_DELAY_MS / 1000.0)
    
    # Assert with tolerance
    assert output_duration >= (expected_min_duration - (TOLERANCE_MS / 1000.0)), (
        f"Duration increase insufficient. "
        f"Input: {input_duration:.3f}s, Output: {output_duration:.3f}s, "
        f"Expected Min: {expected_min_duration:.3f}s. "
        f"Actual Delta: {(output_duration - input_duration)*1000:.1f}ms"
    )
    
    # Sanity check: Output should not be significantly longer than expected
    max_allowed_duration = expected_min_duration + (TOLERANCE_MS / 1000.0)
    assert output_duration <= max_allowed_duration, (
        f"Duration increase excessive. "
        f"Output: {output_duration:.3f}s, Expected Max: {max_allowed_duration:.3f}s"
    )
    
    logger.info("Integration test PASSED: 800ms fixed delay applied correctly.")

def test_latency_injection_jitter_variability(test_environment):
    """
    Integration test: Verify that jitter (±50ms) results in variable but bounded delays.
    
    Steps:
    1. Run LatencyInjector with fixed_delay_ms=800 and jitter_ms=50 (multiple times).
    2. Measure output durations.
    3. Verify that:
       a) Each output duration is within [800-50-TOL, 800+50+TOL] ms of input.
       b) At least two runs produce different durations (proving randomness).
    """
    input_path = test_environment["input_audio"]
    output_paths = [
        test_environment["processed_dir"] / f"test_output_jitter_run{i}.wav"
        for i in range(3)
    ]
    
    input_duration = _get_duration(input_path)
    logger.info(f"Input audio duration: {input_duration:.3f}s")
    
    expected_base_delay_sec = FIXED_DELAY_MS / 1000.0
    jitter_sec = JITTER_MS / 1000.0
    tolerance_sec = TOLERANCE_MS / 1000.0
    
    durations = []
    
    for i, out_path in enumerate(output_paths):
        # Initialize injector with jitter
        injector = LatencyInjector(
            fixed_delay_ms=FIXED_DELAY_MS,
            jitter_ms=JITTER_MS,
            turn_boundaries_path=None,
            logger=logger,
            seed=42 + i  # Deterministic seed per run for reproducibility in testing
        )
        
        try:
            injector.process_file(str(input_path), str(out_path))
        except Exception as e:
            logger.error(f"Latency injection failed on run {i}: {e}")
            pytest.fail(f"LatencyInjector.process_file raised an exception on run {i}: {e}")
        
        assert out_path.exists(), f"Output audio file was not created for run {i}"
        
        out_dur = _get_duration(out_path)
        durations.append(out_dur)
        logger.info(f"Run {i} output duration: {out_dur:.3f}s (Delta: {(out_dur - input_duration)*1000:.1f}ms)")
        
        # Verify bounds: [Base - Jitter - TOL, Base + Jitter + TOL]
        min_expected = input_duration + expected_base_delay_sec - jitter_sec - tolerance_sec
        max_expected = input_duration + expected_base_delay_sec + jitter_sec + tolerance_sec
        
        assert min_expected <= out_dur <= max_expected, (
            f"Run {i} duration out of bounds. "
            f"Got: {out_dur:.3f}s. Expected range: [{min_expected:.3f}s, {max_expected:.3f}s]"
        )
    
    # Verify variability: At least two durations must be different (within float tolerance)
    # Since we use seeds, we expect deterministic different values if jitter is implemented.
    unique_durations = set([round(d, 4) for d in durations])
    assert len(unique_durations) > 1, (
        f"All runs produced identical durations ({durations}). "
        f"Jitter mechanism may not be active or seeds are not varying the output."
    )
    
    logger.info("Integration test PASSED: Jitter variability verified.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])