import os
import json
from typing import Any, Dict, Optional

def load_simulation_params(path: str = "code/simulation_parameters.json") -> Dict[str, Any]:
    """Loads simulation parameters from the JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Simulation parameters file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def get_effect_size_high_low(params: Optional[Dict] = None) -> float:
    """Retrieves the high/low status effect size."""
    if params is None:
        params = load_simulation_params()
    return params.get('effect_sizes', {}).get('status_high', 0.0)

def get_effect_size_interaction(params: Optional[Dict] = None) -> float:
    """Retrieves the interaction effect size."""
    if params is None:
        params = load_simulation_params()
    return params.get('effect_sizes', {}).get('interaction', 0.0)

def get_sample_size(params: Optional[Dict] = None) -> int:
    """Retrieves the sample size N."""
    if params is None:
        params = load_simulation_params()
    return params.get('sample_size', 100)

def get_random_seed(params: Optional[Dict] = None) -> int:
    """Retrieves the random seed."""
    if params is None:
        params = load_simulation_params()
    return params.get('random_seed', 42)

def get_ci_width_warning_threshold(params: Optional[Dict] = None) -> float:
    """Retrieves the CI width warning threshold."""
    if params is None:
        params = load_simulation_params()
    return params.get('ci_width_warning_threshold', 0.5)

def get_injected_interaction_effect(params: Optional[Dict] = None) -> float:
    """Retrieves the injected interaction effect."""
    if params is None:
        params = load_simulation_params()
    return params.get('injected_interaction_effect', 0.0)

def load_family_config(path: str = "data/processed/outcome_type.json") -> str:
    """Loads the outcome type (family) from the processed config."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Outcome type file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    # Map 'binary' to 'binomial', 'continuous' to 'gaussian'
    type_str = data.get('type', 'continuous')
    return 'binomial' if type_str == 'binary' else 'gaussian'

def get_regression_family(family_type: str) -> str:
    """Returns the regression family string."""
    return family_type

def set_regression_family(family_type: str, path: str = "data/processed/model_config.json"):
    """Sets the regression family in the model config."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            config = json.load(f)
        config['family_type'] = family_type
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)

def initialize_config():
    """Initializes default configuration if needed."""
    pass

def load_decision_record(path: str = "code/decision_record.json") -> Dict[str, Any]:
    """Loads the decision record."""
    if not os.path.exists(path):
        return {}
    with open(DECISION_RECORD_PATH, 'r') as f:
        return json.load(f)

def save_decision_record(data: Dict[str, Any], path: str = "code/decision_record.json"):
    """Saves the decision record."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_logging_config() -> Dict[str, Any]:
    """Returns logging configuration."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "code.logger.JSONFormatter"
            }
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "formatter": "json",
                "filename": "logs/app.log"
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json"
            }
        },
        "root": {
            "handlers": ["file", "console"],
            "level": "INFO"
        }
    }

def initialize_logging():
    """Initializes logging based on config."""
    pass