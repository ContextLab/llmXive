"""
Inference model configurations.
"""
from typing import Dict, Any, List

def get_waveform_model(waveform_approx: str = "IMRPhenomPv2") -> Dict[str, Any]:
    """
    Get configuration for the waveform model.
    """
    return {
        "waveform_approximant": waveform_approx,
        "reference_frequency": 20.0,
        "minimum_frequency": 20.0
    }

def get_model_parameters() -> List[str]:
    """Return list of parameters to estimate."""
    return [
        "mass_1", "mass_2", "chi_1", "chi_2", 
        "luminosity_distance", "geocent_time", 
        "phase", "dec", "ra", "theta_jn"
    ]

def get_model_priors() -> Dict[str, Any]:
    """
    Return prior configuration dictionary.
    Note: Actual prior distributions are usually defined in bilby priets files or dicts.
    This returns a placeholder structure for the API.
    """
    return {
        "mass_1": "uniform",
        "mass_2": "uniform",
        "luminosity_distance": "power_law"
        # ... other priors
    }
