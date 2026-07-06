"""
Integration test for inference pipeline: verify convergence on SNR > 10 signal.
Task: T019 [US2]
"""
import os
import sys
import tempfile
import shutil
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import numpy as np
import h5py
import pytest

# Import project modules
from src.data_generation import generate_bbh_waveform, load_or_generate_noise_psd, inject_noise, apply_quantization
from src.utils import calculate_snr, quantize_fixed_fsr
from src.inference_engine import run_inference_single_signal, InferenceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for test
TEST_SEED = 42
TARGET_SNR_MIN = 12.0  # Ensure > 10
TARGET_SNR_MAX = 15.0
TEST_BIT_DEPTH = 16  # High precision to ensure signal is clean
TEST_DURATION = 1.0  # seconds
SAMPLE_RATE = 2048  # Hz

# Ground truth parameters for a single test signal
TEST_M1 = 30.0  # Solar masses
TEST_M2 = 30.0  # Solar masses
TEST_CHI1 = 0.0
TEST_CHI2 = 0.0
TEST_DIST = 200.0  # Mpc
TEST_PHASE = 0.0
TEST_POLARIZATION = 0.0
TEST_RA = 0.0
TEST_DEC = 0.0
TEST_GW_TIME = 0.0
TEST_F_REF = 20.0

class TestInferenceConvergence:
    """
    Integration test verifying that the inference pipeline converges
    on a signal with SNR > 10.
    """

    def _generate_test_signal(self, tmp_path: Path):
        """
        Generates a single high-SNR signal, injects noise, quantizes it,
        and saves it to a temporary HDF5 file.
        Returns the path to the file and the ground truth dict.
        """
        logger.info(f"Generating test signal with seed {TEST_SEED}...")
        np.random.seed(TEST_SEED)

        # 1. Generate Waveform
        # Note: We use a simplified generation here to avoid heavy pycbc/bilby
        # dependencies in the test setup if not strictly necessary, but we
        # aim to match the interface of data_generation.py.
        # For this integration test, we will simulate a realistic waveform
        # using a sine-Gaussian approximation or a simplified IMRPhenomPv
        # if pycbc is available. Given the constraints, we will use a
        # deterministic synthetic signal that mimics the structure required
        # by the inference engine.

        # Create time array
        duration = TEST_DURATION
        sample_rate = SAMPLE_RATE
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        # Simulate a chirp-like signal (simplified for test stability)
        # Chirp frequency increases over time
        f_start = 30.0
        f_end = 100.0
        # Linear chirp approximation for test
        f_t = f_start + (f_end - f_start) * (t / duration)
        
        # Amplitude envelope (rise and fall)
        envelope = np.exp(-((t - duration/2) / (duration/4))**2)
        
        # Phase integration
        phase = 2 * np.pi * np.cumsum(f_t) / sample_rate
        
        # Strain data
        h_plus = envelope * np.sin(phase)
        h_cross = envelope * np.cos(phase)

        # Ground truth
        ground_truth = {
            "m1": TEST_M1,
            "m2": TEST_M2,
            "chi1": TEST_CHI1,
            "chi2": TEST_CHI2,
            "distance": TEST_DIST,
            "phase": TEST_PHASE,
            "polarization": TEST_POLARIZATION,
            "ra": TEST_RA,
            "dec": TEST_DEC,
            "gw_time": TEST_GW_TIME,
            "f_ref": TEST_F_REF,
            "snr_target": (TARGET_SNR_MIN + TARGET_SNR_MAX) / 2
        }

        # 2. Load or Generate Noise PSD
        # For integration test, we generate a synthetic PSD (LIGO-like)
        # f^-4 for low freq, flat for high
        freqs = np.fft.rfftfreq(n_samples, 1/sample_rate)
        psd = np.ones_like(freqs) * 1e-46
        psd[freqs < 20] = 1e-40  # Low freq noise
        psd[freqs > 200] = 1e-47 # High freq noise

        # 3. Inject Noise
        # Scale noise to achieve target SNR
        # SNR^2 = sum( |h|^2 / S_n ) * dt * df ... simplified
        # We scale the signal to match the noise floor to get desired SNR
        signal_power = np.mean(h_plus**2 + h_cross**2)
        noise_power = np.mean(psd)
        
        # Estimate scaling factor for target SNR
        # This is a rough approximation to ensure SNR > 10
        target_snr = (TARGET_SNR_MIN + TARGET_SNR_MAX) / 2
        scaling_factor = target_snr * np.sqrt(noise_power / signal_power) * 0.5 # Safety margin
        
        h_plus_scaled = h_plus * scaling_factor
        h_cross_scaled = h_cross * scaling_factor

        # Generate noise time series
        noise_plus = np.random.normal(0, np.sqrt(np.mean(psd)), n_samples)
        noise_cross = np.random.normal(0, np.sqrt(np.mean(psd)), n_samples)

        # Inject
        data_plus = h_plus_scaled + noise_plus
        data_cross = h_cross_scaled + noise_cross

        # 4. Quantize (16-bit to ensure minimal quantization noise)
        # We need to convert to float, quantize, then back to float
        # Apply quantization to the data
        quantized_plus = apply_quantization(data_plus, bit_depth=TEST_BIT_DEPTH)
        quantized_cross = apply_quantization(data_cross, bit_depth=TEST_BIT_DEPTH)

        # 5. Save to HDF5
        output_file = tmp_path / "test_signal.h5"
        with h5py.File(output_file, "w") as f:
            f.create_dataset("time", data=t)
            f.create_dataset("h_plus", data=quantized_plus)
            f.create_dataset("h_cross", data=quantized_cross)
            f.create_dataset("psd", data=psd)
            f.attrs["sample_rate"] = sample_rate
            f.attrs["duration"] = duration
            f.attrs["ground_truth"] = json.dumps(ground_truth)
            f.attrs["bit_depth"] = TEST_BIT_DEPTH

        logger.info(f"Test signal saved to {output_file}")
        return output_file, ground_truth

    def test_inference_convergence(self):
        """
        Test that the inference engine converges on a signal with SNR > 10.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Generate test data
            signal_path, ground_truth = self._generate_test_signal(tmp_path)

            # Configure Inference
            # We use a simplified config for the test to ensure it runs quickly
            # In a full run, this would be more complex
            config = InferenceConfig(
                signal_file=str(signal_path),
                n_steps=100,  # Small number for test speed
                n_walkers=10,
                bit_depth=TEST_BIT_DEPTH,
                output_file=str(tmp_path / "inference_result.json"),
                priors={
                    "m1": (10.0, 50.0),
                    "m2": (10.0, 50.0),
                    "chi1": (-1.0, 1.0),
                    "chi2": (-1.0, 1.0),
                    "distance": (50.0, 500.0),
                    "phase": (0.0, 2*np.pi),
                },
                true_values=ground_truth
            )

            logger.info("Running inference...")
            try:
                result = run_inference_single_signal(config)
            except Exception as e:
                logger.error(f"Inference failed: {e}")
                # If the engine is not implemented yet, this test might fail.
                # But the task is to write the test that verifies convergence.
                # We assume the engine exists per the task description.
                pytest.fail(f"Inference engine raised an exception: {e}")

            # Verify Convergence
            assert result is not None, "Result should not be None"
            assert "converged" in result, "Result should contain 'converged' status"
            assert result["converged"] is True, "Inference should have converged"

            # Verify Parameter Recovery (within reasonable bounds)
            recovered = result["parameters"]
            
            # Check Chirp Mass (approximate from m1, m2)
            # We check if the recovered values are within the prior bounds and close to truth
            # Since MCMC with 100 steps is short, we check for "plausible" values
            assert "m1" in recovered, "m1 should be recovered"
            assert "m2" in recovered, "m2 should be recovered"
            
            m1_rec = recovered["m1"]
            m2_rec = recovered["m2"]
            
            # Allow for some variance due to short run
            assert 20.0 < m1_rec < 40.0, f"Recovered m1 {m1_rec} not in plausible range"
            assert 20.0 < m2_rec < 40.0, f"Recovered m2 {m2_rec} not in plausible range"

            # Check SNR estimation
            assert "snr" in result, "SNR should be estimated"
            snr_est = result["snr"]
            logger.info(f"Estimated SNR: {snr_est}, Target: {ground_truth['snr_target']}")
            
            # The estimated SNR should be reasonably close to the target (> 10)
            # We allow a wide margin for the short run
            assert snr_est > 8.0, f"Estimated SNR {snr_est} is too low for a high-SNR signal"

            logger.info("Test passed: Inference converged and recovered plausible parameters.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
