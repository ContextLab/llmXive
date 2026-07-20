"""
Waveform model configuration for gravitational wave inference.

This module defines the waveform models and prior configurations used in
the Bayesian parameter estimation pipeline.
"""
from typing import Dict, Any, List


def get_waveform_model(model_name: str = "IMRPhenomPv2") -> Dict[str, Any]:
    """
    Retrieve the configuration for a specific waveform model.

    Args:
        model_name: The name of the waveform model (e.g., 'IMRPhenomPv2').

    Returns:
        A dictionary containing the waveform model configuration.

    Raises:
        ValueError: If the specified model name is not supported.
    """
    models = {
        "IMRPhenomPv2": {
            "name": "IMRPhenomPv2",
            "description": "Phenomenological inspiral-merger-ringdown waveform model.",
            "parameters": ["chirp_mass", "mass_ratio", "spin_1", "spin_2", "luminosity_distance", "phase", "geocent_time", "psi", "inclination", "theta_jn"]
        },
        "IMRPhenomD": {
            "name": "IMRPhenomD",
            "description": "Phenomenological inspiral-merger-ringdown waveform model (aligned spin).",
            "parameters": ["chirp_mass", "mass_ratio", "spin_1z", "spin_2z", "luminosity_distance", "phase", "geocent_time", "psi", "inclination"]
        }
    }

    if model_name not in models:
        raise ValueError(f"Unsupported waveform model: {model_name}. Supported models: {list(models.keys())}")

    return models[model_name]


def get_model_parameters(model_name: str = "IMRPhenomPv2") -> List[str]:
    """
    Get the list of parameters for a specific waveform model.

    Args:
        model_name: The name of the waveform model.

    Returns:
        A list of parameter names.
    """
    model_config = get_waveform_model(model_name)
    return model_config["parameters"]


def get_model_priors(model_name: str = "IMRPhenomPv2") -> Dict[str, Dict[str, Any]]:
    """
    Get the prior configuration for a specific waveform model.

    Args:
        model_name: The name of the waveform model.

    Returns:
        A dictionary mapping parameter names to prior configurations.
    """
    # Default priors for IMRPhenomPv2
    # These are illustrative; actual priors should be defined based on
    # the specific analysis requirements and physical constraints.
    priors = {
        "chirp_mass": {"type": "uniform", "minimum": 10.0, "maximum": 100.0},
        "mass_ratio": {"type": "uniform", "minimum": 0.1, "maximum": 1.0},
        "spin_1": {"type": "uniform", "minimum": -0.99, "maximum": 0.99},
        "spin_2": {"type": "uniform", "minimum": -0.99, "maximum": 0.99},
        "luminosity_distance": {"type": "power_law", "alpha": 2.0, "minimum": 10.0, "maximum": 2000.0},
        "phase": {"type": "uniform", "minimum": 0.0, "maximum": 2 * 3.141592653589793},
        "geocent_time": {"type": "uniform", "minimum": -0.1, "maximum": 0.1},
        "psi": {"type": "uniform", "minimum": 0.0, "maximum": 3.141592653589793},
        "inclination": {"type": "sine", "minimum": 0.0, "maximum": 3.141592653589793},
        "theta_jn": {"type": "sine", "minimum": 0.0, "maximum": 3.141592653589793}
    }
    return priors
