"""
Vibrational Spectrum Data Class Module.

This module defines the `VibrationalSpectrum` data class, which encapsulates
the Vibrational Density of States (VDOS), participation ratio, and frequency bins.
It is designed to work with the `SimulationBox` and `BondNetwork` models in the
project pipeline.

Attributes:
    frequencies (np.ndarray): Frequency bins in THz (float64).
    vdos (np.ndarray): Vibrational Density of States values (float64).
    participation_ratio (np.ndarray): Participation ratio for each frequency bin (float64).
    temperature (float): Temperature at which the spectrum was calculated (K).
    system_size (int): Number of atoms in the system (N).
    calculation_seed (Optional[int]): Random seed used for calculation, if applicable.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class VibrationalSpectrum:
    """
    Data class representing the vibrational spectrum of an amorphous solid.

    This class stores the results of VDOS calculations, including frequency bins,
    the density of states, and the participation ratio indicating the degree of
    localization of vibrational modes.

    Constitution Principle VI Compliance:
        All numerical arrays (frequencies, vdos, participation_ratio) are explicitly
        cast to numpy.float64 to ensure numerical precision and reproducibility.

    Attributes:
        frequencies (np.ndarray): 1D array of frequency bins in THz.
        vdos (np.ndarray): 1D array of VDOS values corresponding to frequencies.
        participation_ratio (np.ndarray): 1D array of participation ratios (0.0 to 1.0).
        temperature (float): Temperature in Kelvin.
        system_size (int): Total number of atoms in the simulation box.
        calculation_seed (Optional[int]): Seed used for stochastic steps (e.g., if applicable).
    """
    frequencies: np.ndarray
    vdos: np.ndarray
    participation_ratio: np.ndarray
    temperature: float
    system_size: int
    calculation_seed: Optional[int] = None

    def __post_init__(self):
        """
        Validates and normalizes the input data.

        Ensures all arrays are numpy.float64 and have consistent shapes.
        """
        # Ensure float64 precision (Constitution Principle VI)
        if not isinstance(self.frequencies, np.ndarray):
            self.frequencies = np.array(self.frequencies, dtype=np.float64)
        else:
            self.frequencies = self.frequencies.astype(np.float64)

        if not isinstance(self.vdos, np.ndarray):
            self.vdos = np.array(self.vdos, dtype=np.float64)
        else:
            self.vdos = self.vdos.astype(np.float64)

        if not isinstance(self.participation_ratio, np.ndarray):
            self.participation_ratio = np.array(self.participation_ratio, dtype=np.float64)
        else:
            self.participation_ratio = self.participation_ratio.astype(np.float64)

        # Validate shapes
        if not (self.frequencies.shape == self.vdos.shape == self.participation_ratio.shape):
            raise ValueError(
                f"Shape mismatch in VibrationalSpectrum: "
                f"frequencies={self.frequencies.shape}, "
                f"vdos={self.vdos.shape}, "
                f"participation_ratio={self.participation_ratio.shape}"
            )

        if self.frequencies.size == 0:
            raise ValueError("VibrationalSpectrum arrays cannot be empty.")

        # Validate physical constraints
        if np.any(self.frequencies < 0):
            raise ValueError("Frequency bins cannot be negative.")
        
        if np.any(self.participation_ratio < 0) or np.any(self.participation_ratio > 1.0):
            # Allow small floating point errors
            if np.any(self.participation_ratio < -1e-6) or np.any(self.participation_ratio > 1.0 + 1e-6):
                raise ValueError("Participation ratio must be between 0.0 and 1.0.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the object to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary containing metadata and array data.
        """
        return {
            "frequencies": self.frequencies.tolist(),
            "vdos": self.vdos.tolist(),
            "participation_ratio": self.participation_ratio.tolist(),
            "temperature": self.temperature,
            "system_size": self.system_size,
            "calculation_seed": self.calculation_seed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VibrationalSpectrum":
        """
        Creates a VibrationalSpectrum instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing the spectrum data.

        Returns:
            VibrationalSpectrum: The reconstructed object.
        """
        return cls(
            frequencies=np.array(data["frequencies"], dtype=np.float64),
            vdos=np.array(data["vdos"], dtype=np.float64),
            participation_ratio=np.array(data["participation_ratio"], dtype=np.float64),
            temperature=float(data["temperature"]),
            system_size=int(data["system_size"]),
            calculation_seed=data.get("calculation_seed")
        )

    def get_localized_mode_count(self, threshold: float = 0.2) -> int:
        """
        Counts the number of modes with a participation ratio below a threshold.

        Low participation ratio indicates localized modes.

        Args:
            threshold (float): The upper bound for PR to be considered localized.
                               Default is 0.2.

        Returns:
            int: Number of localized modes.
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0.")
        
        return int(np.sum(self.participation_ratio < threshold))

    def get_acoustic_mode_check(self, epsilon: float = 1e-6) -> bool:
        """
        Checks if the lowest frequency modes have non-zero VDOS (acoustic modes).

        Args:
            epsilon (float): Minimum threshold for VDOS to be considered non-zero.

        Returns:
            bool: True if acoustic modes are present (VDOS > epsilon at low freq), False otherwise.
        """
        if self.frequencies.size == 0:
            return False
        
        # Check the first few bins (assuming sorted frequencies)
        low_freq_mask = self.frequencies < 0.1  # 0.1 THz cutoff for acoustic check
        if np.any(low_freq_mask):
            return bool(np.any(self.vdos[low_freq_mask] > epsilon))
        return False

    def __repr__(self) -> str:
        return (
            f"VibrationalSpectrum(system_size={self.system_size}, "
            f"temperature={self.temperature}K, "
            f"n_bins={len(self.frequencies)}, "
            f"localized_modes={self.get_localized_mode_count()})"
        )