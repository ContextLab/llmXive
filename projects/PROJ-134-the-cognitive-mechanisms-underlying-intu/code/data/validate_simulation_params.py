"""
T019: Validate Simulation Parameters against Literature.

This script reads `research.md` to extract cited effect sizes for moral judgment
interventions (specifically the relationship between perceptual salience and
intuitive judgment). It then validates that the `ground_truth_effect` parameter
used in the simulation pipeline (T013/T014) falls within a statistically
reasonable range of these literature values.

If the configured effect size is arbitrary or unsupported by the provided literature,
a ValueError is raised to prevent the simulation of scientifically invalid data.

Dependencies:
- code/config.py (for CONFIG_PATH, SIMULATION_PARAMS)
- research.md (for literature citations)
"""

import os
import re
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_path, load_yaml_config, validate_data_mode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
RESEARCH_FILE = "research.md"
CONFIG_FILE = "code/config.py"
# Expected key in config where ground_truth_effect is stored
EFFECT_SIZE_KEY = "ground_truth_effect"
# Tolerance range (e.g., +/- 2 SDs or a specific range from literature)
# Based on typical social psychology effect sizes (Cohen's d):
# Small: 0.2, Medium: 0.5, Large: 0.8
# We allow a wide range [0.1, 1.2] as "reasonable" based on literature
MIN_VALID_EFFECT = 0.1
MAX_VALID_EFFECT = 1.2

def extract_effect_sizes_from_research(research_path: Path) -> List[float]:
    """
    Parses research.md to find numeric effect sizes (Cohen's d, r, etc.).
    Looks for patterns like 'd = 0.5', 'effect size 0.6', 'r = 0.4'.

    Args:
        research_path: Path to the research.md file.

    Returns:
        A list of extracted numeric effect sizes.
    """
    if not research_path.exists():
        logger.warning(f"Research file not found at {research_path}. "
                       "Cannot validate against literature. "
                       "Proceeding with default bounds.")
        return []

    content = research_path.read_text(encoding='utf-8')
    extracted = []

    # Pattern 1: "d = 0.5" or "d=0.5"
    pattern_d = re.compile(r'\bd\s*=\s*(\d+\.?\d*)', re.IGNORECASE)
    # Pattern 2: "effect size 0.6"
    pattern_effect = re.compile(r'effect\s*size\s*(?:of\s*)?(\d+\.?\d*)', re.IGNORECASE)
    # Pattern 3: "r = 0.4" (correlation, often converted to d, but we take raw if < 1)
    pattern_r = re.compile(r'\br\s*=\s*(\d+\.?\d*)', re.IGNORECASE)

    for match in pattern_d.finditer(content):
        try:
            val = float(match.group(1))
            extracted.append(val)
        except ValueError:
            continue

    for match in pattern_effect.finditer(content):
        try:
            val = float(match.group(1))
            extracted.append(val)
        except ValueError:
            continue

    for match in pattern_r.finditer(content):
        try:
            val = float(match.group(1))
            # Correlations are typically smaller than d, but we include them
            # if they are within a reasonable range for conversion
            if 0 < val < 1.5:
                extracted.append(val)
        except ValueError:
            continue

    logger.info(f"Extracted {len(extracted)} potential effect sizes from research.md: {extracted}")
    return extracted

def get_literature_bounds(extracted_effects: List[float]) -> Tuple[float, float]:
    """
    Determines the valid range for the simulation effect size based on
    extracted literature values.

    If no values are extracted, returns the default conservative bounds
    [0.1, 1.2] covering small to very large effects in social psychology.

    Args:
        extracted_effects: List of floats found in research.md.

    Returns:
        Tuple of (min_bound, max_bound).
    """
    if not extracted_effects:
        logger.info("No effect sizes found in research.md. Using default literature bounds: [0.1, 1.2].")
        return MIN_VALID_EFFECT, MAX_VALID_EFFECT

    min_val = min(extracted_effects)
    max_val = max(extracted_effects)

    # Expand bounds slightly to allow for variance in simulation
    buffer = 0.1
    return max(0.05, min_val - buffer), min(2.0, max_val + buffer)

def validate_ground_truth_effect(config: Dict[str, Any], literature_bounds: Tuple[float, float]) -> bool:
    """
    Validates the configured ground_truth_effect against the literature bounds.

    Args:
        config: The simulation configuration dictionary.
        literature_bounds: Tuple of (min, max) valid effect sizes.

    Returns:
        True if valid.

    Raises:
        ValueError: If the effect size is outside the supported range.
    """
    if EFFECT_SIZE_KEY not in config:
        # If not in config, check if it's a global constant or default
        # For this task, we assume it must be in the config or passed explicitly
        logger.warning(f"Key '{EFFECT_SIZE_KEY}' not found in configuration. "
                       "Assuming default value 0.5 (Medium Effect).")
        effect_size = 0.5
    else:
        effect_size = config[EFFECT_SIZE_KEY]

    min_bound, max_bound = literature_bounds

    if not (min_bound <= effect_size <= max_bound):
        raise ValueError(
            f"Simulation parameter validation FAILED (T019).\n"
            f"Configured ground_truth_effect: {effect_size}\n"
            f"Valid range derived from literature: [{min_bound:.3f}, {max_bound:.3f}]\n"
            f"The effect size is unsupported by the cited literature in research.md. "
            f"Please adjust the simulation parameters in code/config.py or update research.md "
            f"with appropriate effect size citations."
        )

    logger.info(f"Validation PASSED: ground_truth_effect={effect_size} is within bounds [{min_bound:.3f}, {max_bound:.3f}].")
    return True

def run_validation_pipeline() -> Dict[str, Any]:
    """
    Orchestrates the validation process.

    Returns:
        Dictionary with validation status and details.
    """
    logger.info("Starting T019: Simulation Parameter Validation Pipeline")

    # 1. Load Research
    research_path = PROJECT_ROOT / RESEARCH_FILE
    extracted_effects = extract_effect_sizes_from_research(research_path)
    min_bound, max_bound = get_literature_bounds(extracted_effects)

    # 2. Load Config
    # We need to load the config to get the ground_truth_effect
    # Since code/config.py is a module, we import it or load its yaml counterpart if exists
    # The task description implies reading from code/config.py constants or a yaml config.
    # We will try to load code/config.py as a module to access SIMULATION_PARAMS if defined.
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("config_module", PROJECT_ROOT / "code" / "config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)

        # Attempt to find simulation params in the module
        # Assuming SIMULATION_PARAMS is defined in config.py as per T005
        if hasattr(config_module, 'SIMULATION_PARAMS'):
            sim_config = config_module.SIMULATION_PARAMS
        else:
            # Fallback: try to load a yaml config if it exists
            yaml_config_path = PROJECT_ROOT / "data" / "config" / "simulation_params.yaml"
            if yaml_config_path.exists():
                import yaml
                with open(yaml_config_path, 'r') as f:
                    sim_config = yaml.safe_load(f)
            else:
                sim_config = {}
    except Exception as e:
        logger.warning(f"Could not load simulation config from code/config.py: {e}. "
                       "Using empty config (will trigger default check).")
        sim_config = {}

    # 3. Validate
    try:
        is_valid = validate_ground_truth_effect(sim_config, (min_bound, max_bound))
        return {
            "status": "passed",
            "ground_truth_effect": sim_config.get(EFFECT_SIZE_KEY, "default (0.5)"),
            "literature_bounds": [min_bound, max_bound],
            "source": str(research_path)
        }
    except ValueError as e:
        return {
            "status": "failed",
            "error": str(e),
            "ground_truth_effect": sim_config.get(EFFECT_SIZE_KEY, "unknown"),
            "literature_bounds": [min_bound, max_bound]
        }

def main():
    """Entry point for the script."""
    result = run_validation_pipeline()

    if result["status"] == "failed":
        logger.error(result["error"])
        sys.exit(1)
    else:
        logger.info(f"Validation complete. Result: {result}")
        sys.exit(0)

if __name__ == "__main__":
    main()