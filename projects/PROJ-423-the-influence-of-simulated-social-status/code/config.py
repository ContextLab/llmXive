import os
import json
from typing import Any, Dict, Optional

DECISION_RECORD_PATH = "code/decision_record.json"
SIMULATION_PARAMS_PATH = "code/simulation_parameters.json"

def load_decision_record() -> Dict:
    """Loads the decision record."""
    if not os.path.exists(DECISION_RECORD_PATH):
        return {}
    with open(DECISION_RECORD_PATH, 'r') as f:
        return json.load(f)

def save_decision_record(data: Dict) -> None:
    """Saves the decision record."""
    with open(DECISION_RECORD_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_simulation_params() -> Dict:
    """Loads simulation parameters."""
    if not os.path.exists(SIMULATION_PARAMS_PATH):
        return {}
    with open(SIMULATION_PARAMS_PATH, 'r') as f:
        return json.load(f)

def get_effect_size_high_low() -> float:
    """Retrieves the effect size for High vs Low status."""
    params = load_simulation_params()
    return params.get("effect_sizes", {}).get("status_high", 0.0)

def get_effect_size_interaction() -> float:
    """Retrieves the interaction effect size."""
    params = load_simulation_params()
    return params.get("effect_sizes", {}).get("interaction", 0.0)

def get_sample_size() -> int:
    """Retrieves the sample size."""
    params = load_simulation_params()
    return params.get("sample_size", 100)

def get_random_seed() -> int:
    """Retrieves the random seed."""
    params = load_simulation_params()
    return params.get("random_seed", 42)

def set_regression_family(family: str) -> None:
    """Sets the regression family in the decision record."""
    record = load_decision_record()
    record["regression_family"] = family
    save_decision_record(record)

def get_regression_family() -> str:
    """Gets the regression family."""
    record = load_decision_record()
    return record.get("regression_family", "gaussian")

def load_family_config() -> Dict:
    """Loads family configuration."""
    return {"family": get_regression_family()}

def initialize_config() -> None:
    """Initializes configuration files if they don't exist."""
    if not os.path.exists(DECISION_RECORD_PATH):
        save_decision_record({})
    if not os.path.exists(SIMULATION_PARAMS_PATH):
        # Default params if missing
        save_decision_record({
            "effect_sizes": {
                "status_high": 0.5,
                "status_low": -0.5,
                "observed_risky": 0.3,
                "observed_conservative": -0.3,
                "interaction": 0.2
            },
            "sample_size": 100,
            "random_seed": 42
        })
