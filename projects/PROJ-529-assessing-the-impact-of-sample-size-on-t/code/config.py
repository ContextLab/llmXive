import os
from typing import Optional

# Environment-based configuration for data source selection
# Supports 'real' (Cochrane/Campbell) and 'simulation' modes
DATA_SOURCE = os.getenv("DATA_SOURCE", "simulation")

# Thresholds for stability and coverage analysis
# These constants satisfy FR-007 and SC-003 requirements.
# NOMINAL_COVERAGE_TARGET: The target CI coverage rate (95%) used in T034
#   to identify the minimum k where coverage stabilizes within ±2%.
# STABILITY_THRESHOLD: The derivative threshold (0.05 change in SD per unit k)
#   used in T032 to detect the inflection point where diminishing returns begin.
NOMINAL_COVERAGE_TARGET = 0.95
STABILITY_THRESHOLD = 0.05

# Simulation parameters (fallback mode)
# Used by T019 when real data acquisition fails
SIMULATION_TAU_SQ = 0.04
SIMULATION_MEAN_EFFECT = 0.3
SIMULATION_BIAS = 0.1
SIMULATION_STUDY_COUNT_RANGE = (3, 50)

def get_config_summary() -> dict:
    """
    Returns a summary of the current configuration.
    This function is part of the existing API surface.
    """
    return {
        "python_version": "3.11",
        "data_source": DATA_SOURCE,
        "nominal_coverage_target": NOMINAL_COVERAGE_TARGET,
        "stability_threshold": STABILITY_THRESHOLD,
        "simulation_params": {
            "tau_sq": SIMULATION_TAU_SQ,
            "mean_effect": SIMULATION_MEAN_EFFECT,
            "bias": SIMULATION_BIAS,
            "study_count_range": SIMULATION_STUDY_COUNT_RANGE
        }
    }