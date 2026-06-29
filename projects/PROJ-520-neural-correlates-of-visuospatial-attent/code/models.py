"""
Data model entities for the neural correlates analysis pipeline.
Defines core structures for Epochs, Features, and Classification results.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class Epoch:
    """Represents a single EEG epoch."""
    id: str
    condition: str  # 'active' or 'passive'
    data: np.ndarray  # Shape: (channels, time_points)
    times: np.ndarray
    events: Dict[str, Any] = field(default_factory=dict)

    def get_power(self, freq_range: tuple) -> float:
        """Calculate mean power within a specific frequency range using FFT.
        
        Args:
            freq_range: Tuple of (low_freq, high_freq) in Hz.
        
        Returns:
            Mean power value across all channels and time points for the given band.
        """
        if len(self.data.shape) != 2:
            raise ValueError("Data must be 2D (channels, time_points) for FFT.")
        
        # Perform FFT on each channel
        fft_data = np.fft.rfft(self.data, axis=1)
        frequencies = np.fft.rfftfreq(self.data.shape[1], d=self.times[1] - self.times[0])
        
        # Identify indices within the frequency range
        freq_mask = (frequencies >= freq_range[0]) & (frequencies < freq_range[1])
        
        if not np.any(freq_mask):
            return 0.0
        
        # Calculate power (magnitude squared)
        power_spectrum = np.abs(fft_data) ** 2
        
        # Average power across the selected frequency band and all channels/time
        mean_power = np.mean(power_spectrum[:, freq_mask])
        return float(mean_power)

@dataclass
class Feature:
    """Represents a single extracted feature."""
    name: str
    value: float
    electrode: str
    frequency_band: str  # 'alpha', 'beta', etc.
    epoch_id: str

@dataclass
class ClassifierResult:
    """Stores results from a classification run."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: np.ndarray
    cv_scores: List[float]
    permutation_p_value: Optional[float] = None
    is_significant: Optional[bool] = None

@dataclass
class PreprocessingReport:
    """Summary of preprocessing steps applied."""
    raw_channels: int
    cleaned_channels: int
    rejected_components: List[int]
    skipped_electrodes: List[str] = field(default_factory=list)
    event_source: str = "markers"  # or "landmark_fallback"
    epoch_count_active: int = 0
    epoch_count_passive: int = 0
    is_underpowered: bool = False

@dataclass
class FeatureMetadata:
    """Metadata describing the feature matrix."""
    n_epochs: int
    n_features: int
    electrode_list: List[str]
    frequency_bands: List[str]
    correlation_matrix: Optional[np.ndarray] = None
    fwe_corrected_p_values: Dict[str, float] = field(default_factory=dict)