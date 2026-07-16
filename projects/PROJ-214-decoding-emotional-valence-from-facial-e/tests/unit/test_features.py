"""
Unit tests for feature extraction functions (RMS, ZCR, WAMP, MAV).
"""
import pytest
import numpy as np
from code.preprocessing import extract_rms, extract_zcr, extract_wamp, extract_mav


class TestExtractRMS:
    """Tests for extract_rms function."""

    def test_rms_constant_signal(self):
        """Verify RMS of constant signal equals absolute value of constant."""
        constant = 5.0
        signal = np.ones(100) * constant
        rms = extract_rms(signal)
        assert np.isclose(rms, np.abs(constant))

    def test_rms_zero_signal(self):
        """Verify RMS of zero signal is zero."""
        signal = np.zeros(100)
        rms = extract_rms(signal)
        assert rms == 0.0

    def test_rms_sine_wave(self):
        """Verify RMS of sine wave is amplitude / sqrt(2)."""
        amplitude = 2.0
        fs = 1000
        t = np.linspace(0, 1, fs)
        signal = amplitude * np.sin(2 * np.pi * 50 * t)
        rms = extract_rms(signal)
        expected = amplitude / np.sqrt(2)
        assert np.isclose(rms, expected, rtol=0.01)


class TestExtractZCR:
    """Tests for extract_zcr function."""

    def test_zcr_constant_positive(self):
        """Verify ZCR of constant positive signal is zero."""
        signal = np.ones(100) * 5.0
        zcr = extract_zcr(signal)
        assert zcr == 0

    def test_zcr_constant_negative(self):
        """Verify ZCR of constant negative signal is zero."""
        signal = np.ones(100) * -5.0
        zcr = extract_zcr(signal)
        assert zcr == 0

    def test_zcr_sine_wave(self):
        """Verify ZCR of sine wave is approximately 2 * frequency."""
        fs = 1000
        freq = 10  # 10 Hz
        t = np.linspace(0, 1, fs)
        signal = np.sin(2 * np.pi * freq * t)
        zcr = extract_zcr(signal)
        # Should be roughly 2 crossings per cycle
        expected = 2 * freq
        assert np.isclose(zcr, expected, rtol=0.1)


class TestExtractWAMP:
    """Tests for extract_wamp function."""

    def test_wamp_threshold(self):
        """Verify WAMP counts crossings above threshold."""
        threshold = 0.5
        # Create a signal that crosses threshold twice
        signal = np.array([0.0, 0.6, 0.0, -0.6, 0.0])
        wamp = extract_wamp(signal, threshold)
        # Crossings: 0->0.6 (1), 0.6->0 (2), 0->-0.6 (3), -0.6->0 (4)
        # But WAMP counts pairs where |x[i] - x[i-1]| > threshold
        # 0->0.6: diff=0.6 > 0.5 (1)
        # 0.6->0: diff=0.6 > 0.5 (2)
        # 0->-0.6: diff=0.6 > 0.5 (3)
        # -0.6->0: diff=0.6 > 0.5 (4)
        assert wamp == 4

    def test_wamp_no_crossings(self):
        """Verify WAMP is zero if no threshold crossings."""
        threshold = 0.5
        signal = np.array([0.1, 0.2, 0.3, 0.4])
        wamp = extract_wamp(signal, threshold)
        assert wamp == 0


class TestExtractMAV:
    """Tests for extract_mav function."""

    def test_mav_constant_signal(self):
        """Verify MAV of constant signal equals absolute value of constant."""
        constant = 5.0
        signal = np.ones(100) * constant
        mav = extract_mav(signal)
        assert mav == np.abs(constant)

    def test_mav_zero_signal(self):
        """Verify MAV of zero signal is zero."""
        signal = np.zeros(100)
        mav = extract_mav(signal)
        assert mav == 0.0

    def test_mav_symmetric_signal(self):
        """Verify MAV of symmetric positive/negative signal."""
        signal = np.array([1.0, -1.0, 1.0, -1.0])
        mav = extract_mav(signal)
        expected = 1.0
        assert np.isclose(mav, expected)
