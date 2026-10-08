import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Literal, Dict, Any
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

# Enums defined as Literal types for simplicity and JSON compatibility
MissingMechanism = Literal["MCAR", "MAR", "MNAR"]
AnalysisMethod = Literal["CC", "MI", "IPW"]
OutcomeType = Literal["continuous", "binary"]

@dataclass
class SimulationConfig:
    """
    Configuration for a single simulation condition.
    
    Attributes:
        dataset_id: OpenML ID of the RCT dataset to use.
        mechanism: Missing data mechanism (MCAR, MAR, MNAR).
        missing_rate: Fraction of data to simulate as missing (0.0 to 1.0).
        outcome_type: Type of outcome variable ('continuous' or 'binary').
        seed: Random seed for reproducibility.
        iterations: Number of simulation iterations for this condition.
        analysis_method: Method to handle missing data ('CC', 'MI', 'IPW').
        alternative_hypothesis: If True, simulate effect (d=0.5) for power analysis.
        covariate_for_mar: Optional name of covariate to use for MAR simulation.
    """
    dataset_id: int
    mechanism: MissingMechanism
    missing_rate: float
    outcome_type: OutcomeType
    seed: int
    iterations: int = 1000
    analysis_method: AnalysisMethod = "CC"
    alternative_hypothesis: bool = False
    covariate_for_mar: Optional[str] = None
    
    def __post_init__(self):
        # Validate ranges
        if not 0.0 <= self.missing_rate <= 1.0:
            raise ValueError(f"missing_rate must be between 0.0 and 1.0, got {self.missing_rate}")
        
        valid_mechanisms = ["MCAR", "MAR", "MNAR"]
        if self.mechanism not in valid_mechanisms:
            raise ValueError(f"mechanism must be one of {valid_mechanisms}, got {self.mechanism}")
        
        valid_outcomes = ["continuous", "binary"]
        if self.outcome_type not in valid_outcomes:
            raise ValueError(f"outcome_type must be one of {valid_outcomes}, got {self.outcome_type}")
        
        valid_methods = ["CC", "MI", "IPW"]
        if self.analysis_method not in valid_methods:
            raise ValueError(f"analysis_method must be one of {valid_methods}, got {self.analysis_method}")

def load_config(config_path: str) -> SimulationConfig:
    """
    Load a SimulationConfig from a JSON file.
    
    Args:
        config_path: Path to the JSON configuration file.
        
    Returns:
        A validated SimulationConfig object.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the JSON is invalid or missing required fields.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Validate required fields
    required_fields = ["dataset_id", "mechanism", "missing_rate", "outcome_type", "seed"]
    for field_name in required_fields:
        if field_name not in data:
            raise ValueError(f"Missing required field in config: {field_name}")
    
    return SimulationConfig(
        dataset_id=data["dataset_id"],
        mechanism=data["mechanism"],
        missing_rate=float(data["missing_rate"]),
        outcome_type=data["outcome_type"],
        seed=int(data["seed"]),
        iterations=data.get("iterations", 1000),
        analysis_method=data.get("analysis_method", "CC"),
        alternative_hypothesis=data.get("alternative_hypothesis", False),
        covariate_for_mar=data.get("covariate_for_mar", None)
    )

def validate_config(config: SimulationConfig) -> bool:
    """
    Perform additional runtime validation on a SimulationConfig.
    
    Args:
        config: The configuration to validate.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    # Basic dataclass validation is done in __post_init__
    # Additional checks can be added here if needed
    
    if config.iterations < 1:
        raise ValueError(f"iterations must be at least 1, got {config.iterations}")
        
    if config.missing_rate == 1.0 and config.analysis_method == "CC":
        # Edge case: 100% missingness with Complete Case analysis yields no data
        logger.warning("100% missingness with CC method will result in empty dataset.")
        
    return True

def config_to_dict(config: SimulationConfig) -> Dict[str, Any]:
    """
    Convert a SimulationConfig to a dictionary for serialization.
    
    Args:
        config: The configuration to convert.
        
    Returns:
        A dictionary representation of the config.
    """
    return asdict(config)

def save_config(config: SimulationConfig, output_path: str) -> None:
    """
    Save a SimulationConfig to a JSON file.
    
    Args:
        config: The configuration to save.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(config_to_dict(config), f, indent=2)
        
    logger.info(f"Configuration saved to {output_path}")