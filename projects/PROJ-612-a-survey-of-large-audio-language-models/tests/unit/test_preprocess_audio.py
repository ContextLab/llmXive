"""
Unit tests for the audio preprocessing module (T013).
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
import numpy as np

# Mock librosa to avoid heavy dependencies in unit tests if needed, 
# but here we assume librosa is available as per requirements.
# If librosa is not installed in the test environment, this test suite 
# would need to mock the import. For this task, we assume a standard env.
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

# We need to import the module under test
# Since the module uses relative imports or absolute imports from 'code', 
# we assume the test is run from the project root with code/ in sys.path
# or we adjust sys.path.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocess_audio import (
    resample_audio,
    process_sample,
    MAX_DURATION_SECONDS,
    TARGET_SAMPLE_RATE
)

class TestResampleAudio(unittest.TestCase):
    def setUp(self):
        if not HAS_LIBROSA:
            self.skipTest("librosa is not installed")

    def test_resample_same_rate(self):
        """Test that resampling to the same rate returns the same data."""
        audio = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sr = 16000
        result = resample_audio(audio, sr, sr)
        np.testing.assert_array_equal(audio, result)

    def test_resample_different_rate(self):
        """Test resampling from 8kHz to 16kHz."""
        # Create a simple sine wave
        sr_orig = 8000
        sr_target = 16000
        duration = 0.1  # 0.1 seconds
        t = np.linspace(0, duration, int(sr_orig * duration))
        freq = 440
        audio = np.sin(2 * np.pi * freq * t)
        
        result = resample_audio(audio, sr_orig, sr_target)
        
        # Check length is approximately doubled
        expected_len = int(len(audio) * (sr_target / sr_orig))
        self.assertAlmostEqual(len(result), expected_len, delta=expected_len * 0.1)
        self.assertEqual(result.dtype, audio.dtype)

class TestProcessSample(unittest.TestCase):
    def setUp(self):
        if not HAS_LIBROSA:
            self.skipTest("librosa is not installed")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_wav_file(self, duration_seconds, sr=16000):
        """Helper to create a dummy WAV file."""
        import wave
        import struct
        
        n_channels = 1
        sampwidth = 2  # 16-bit
        n_frames = int(duration_seconds * sr)
        filename = os.path.join(self.temp_dir, f"test_{duration_seconds}s.wav")
        
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(n_channels)
            wav_file.setsampwidth(sampwidth)
            wav_file.setframerate(sr)
            for i in range(n_frames):
                # Generate a simple tone
                val = int(32767 * np.sin(2 * np.pi * 440 * i / sr))
                packed_val = struct.pack('<h', val)
                wav_file.writeframes(packed_val)
        
        return Path(filename)

    def test_process_valid_sample(self):
        """Test processing a valid sample (< 10s)."""
        duration = 5.0
        file_path = self._create_wav_file(duration)
        
        sample_obj, was_discarded = process_sample(file_path, "speech")
        
        self.assertIsNotNone(sample_obj)
        self.assertFalse(was_discarded)
        self.assertEqual(sample_obj.domain, "speech")
        self.assertAlmostEqual(sample_obj.duration, duration, delta=0.5) # Allow some tolerance
        self.assertEqual(sample_obj.sample_rate, TARGET_SAMPLE_RATE)

    def test_process_discard_long_sample(self):
        """Test that a sample > 10s is discarded."""
        duration = 15.0
        file_path = self._create_wav_file(duration)
        
        sample_obj, was_discarded = process_sample(file_path, "music")
        
        self.assertIsNone(sample_obj)
        self.assertTrue(was_discarded)

    def test_process_missing_file(self):
        """Test processing a non-existent file."""
        file_path = Path(self.temp_dir) / "non_existent.wav"
        
        sample_obj, was_discarded = process_sample(file_path, "env")
        
        self.assertIsNone(sample_obj)
        self.assertTrue(was_discarded)

if __name__ == '__main__':
    unittest.main()