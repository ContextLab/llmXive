import os
import sys
import time
import logging
import mne
import numpy as np
from pathlib import Path

from exclusion_logic import run_exclusion_check
from synchrony import get_logger

logger = get_logger(__name__)

def component_rejection(ica, data, ch_names, fmin=30, fmax=None):
    """
    Identifies and removes ICA components exhibiting a kurtosis > 5 or a spectral peak > 30 Hz.
    """
    ica.fit(data, picks=ch_names)
    ica.exclude = []
    for i in range(ica.n_components_):
        kurtosis = ica.scores_[i].kurtosis()
        if kurtosis > 5:
            logger.info(f"Component {i} excluded due to high kurtosis: {kurtosis:.2f}")
            ica.exclude.append(i)
            continue

        # Spectral peak detection
        try:
            sfreq = data.info['sfreq']
            psd = ica.scores_[:, i]
            freqs = np.fft.fftfreq(psd.shape[0], d=1/sfreq)
            psd = np.abs(np.fft.fft(psd))
            peak_freq = freqs[np.argmax(psd[freqs > 0])]
            if peak_freq > fmax or (fmin is not None and peak_freq > fmin):
                logger.info(f"Component {i} excluded due to high spectral peak: {peak_freq:.2f} Hz")
                ica.exclude.append(i)
        except Exception as e:
            logger.warning(f"Error calculating spectral peak for component {i}: {e}")

    ica.apply(data)
    return ica, data

def main():
    # This function is not directly used in this task.
    # It's included to maintain consistency with other preprocess.py files.
    pass

if __name__ == '__main__':
    main()