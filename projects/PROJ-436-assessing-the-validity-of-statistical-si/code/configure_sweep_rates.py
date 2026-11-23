"""
configure_sweep_rates.py

Configures and populates SimulationConfig with the required sweep rates
for the sensitivity analysis (User Story 2).

This script defines the range of missingness rates to test and ensures
the configuration is valid before the sensitivity sweep is executed.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure imports work when run as a script or imported
if __name__ == "__main__":
    # Add parent directory to path for imports if running directly
    sys.path.insert(0, str(Path(__file__).parent))

from config import SimulationConfig, MissingMechanism, AnalysisMethod, OutcomeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_sweep_rates(
    dataset_id: int = 1468,  # Default OpenML ID (e.g., a standard RCT dataset)
    mechanisms: List[str] = None,
    methods: List[str] = None,
    outcome_type: str = "continuous",
    iterations: int = 500,
    seed: int = 42,
    missing_rate_range: List[float] = None
) -> SimulationConfig:
    """
    Configures a SimulationConfig object with the specific sweep parameters
    required for User Story 2 (Sensitivity Analysis).

    Args:
        dataset_id: OpenML dataset ID to use.
        mechanisms: List of missingness mechanisms (MCAR, MAR, MNAR).
        methods: List of analysis methods (CC, MI, IPW).
        outcome_type: Type of outcome ('continuous' or 'binary').
        iterations: Number of simulation iterations per condition.
        seed: Random seed for reproducibility.
        missing_rate_range: List of missingness rates to sweep.
                            Defaults to [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
                            if not provided.

    Returns:
        A populated SimulationConfig object ready for the sensitivity sweep.
    """
    if mechanisms is None:
        mechanisms = ["mcar", "mar", "mnar"]
    if methods is None:
        methods = ["cc", "mi", "ipw"]
    
    # Define the sweep rates as per the requirement for incremental steps
    # The task description implies a range of values. A common range is 0 to 70%
    # in steps of 10%.
    if missing_rate_range is None:
        missing_rate_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

    # Validate mechanisms
    valid_mechanisms = ["mcar", "mar", "mnar"]
    for m in mechanisms:
        if m not in valid_mechanisms:
            raise ValueError(f"Invalid mechanism '{m}'. Must be one of {valid_mechanisms}")

    # Validate methods
    valid_methods = ["cc", "mi", "ipw"]
    for m in methods:
        if m not in valid_methods:
            raise ValueError(f"Invalid method '{m}'. Must be one of {valid_methods}")

    # Validate outcome type
    if outcome_type not in ["continuous", "binary"]:
        raise ValueError(f"Invalid outcome_type '{outcome_type}'. Must be 'continuous' or 'binary'")

    logger.info(f"Configuring sweep with {len(missing_rate_range)} rates: {missing_rate_range}")
    logger.info(f"Mechanisms: {mechanisms}")
    logger.info(f"Methods: {methods}")
    logger.info(f"Total conditions to test: {len(missing_rate_range) * len(mechanisms) * len(methods)}")

    # Construct the config
    config = SimulationConfig(
        dataset_id=dataset_id,
        missing_mechanisms=mechanisms,
        analysis_methods=methods,
        outcome_type=outcome_type,
        missing_rates=missing_rate_range,
        iterations=iterations,
        seed=seed
    )

    return config

def main():
    """
    Main entry point to generate and save the sweep configuration.
    This is typically called by main.py or run directly to inspect the config.
    """
    logger.info("Starting sweep rate configuration...")

    # Example configuration for the sensitivity analysis
    # We use a standard set of rates: 0%, 10%, ..., 70%
    config = configure_sweep_rates(
        dataset_id=1468,
        mechanisms=["mcar", "mar", "mnar"],
        methods=["cc", "mi", "ipw"],
        outcome_type="continuous",
        iterations=500,
        seed=42,
        missing_rate_range=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    )

    # Save the configuration to a JSON file for downstream use
    output_path = Path("data/processed/sweep_config.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config_dict = config.to_dict() if hasattr(config, 'to_dict') else config.__dict__
    
    with open(output_path, 'w') as f:
        json.dump(config_dict, f, indent=2)

    logger.info(f"Sweep configuration saved to {output_path}")
    logger.info(f"Total conditions: {len(config.missing_rates) * len(config.missing_mechanisms) * len(config.analysis_methods)}")
    
    return config

if __name__ == "__main__":
    main()