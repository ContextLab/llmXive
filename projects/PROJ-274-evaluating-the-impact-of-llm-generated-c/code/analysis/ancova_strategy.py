"""
ANCOVA Strategy Implementation for FR-009.

This module implements the primary analysis strategy mandated by the Plan's
"Key Methodological Updates": replacing the "perfect matching" strategy
with ANCOVA adjustment using repository-level covariates.

It consumes `data/raw/repo_covariates.json` (produced by T021e) and
generates `data/raw/ancova_strategy_config.json` to document the
configuration of the adjustment.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Output path as specified in tasks.md
COVARIATES_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "repo_covariates.json"
OUTPUT_CONFIG_PATH = PROJECT_ROOT / "data" / "raw" / "ancova_strategy_config.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_covariates() -> Dict[str, Any]:
    """
    Load the repository covariates JSON.
    
    Raises:
        FileNotFoundError: If the covariates file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not COVARIATES_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Covariate file not found at {COVARIATES_INPUT_PATH}. "
            "Ensure T021e (generate_covariates_json) has been executed successfully."
        )
    
    with open(COVARIATES_INPUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_covariate_structure(data: Dict[str, Any]) -> bool:
    """
    Validate that the loaded data contains the expected keys for ANCOVA.
    
    Expected keys (based on T021e output):
    - 'loc': Lines of Code (numeric)
    - 'cc': Cyclomatic Complexity (numeric)
    - 'doc_quality': Human Documentation Quality Score (numeric)
    - 'repo_id': Identifier for the repository
    
    Returns:
        True if structure is valid, False otherwise.
    """
    required_keys = {'loc', 'cc', 'doc_quality', 'repo_id'}
    if not isinstance(data, list):
        logger.error("Covariate data must be a list of records.")
        return False
    
    if not data:
        logger.warning("Covariate data is empty.")
        return False
    
    first_record = data[0]
    missing_keys = required_keys - set(first_record.keys())
    if missing_keys:
        logger.error(f"Missing required keys in covariate data: {missing_keys}")
        return False
    
    # Validate numeric types
    for key in ['loc', 'cc', 'doc_quality']:
        if not isinstance(first_record[key], (int, float)):
            logger.error(f"Key '{key}' must be numeric, found {type(first_record[key])}")
            return False
    
    return True


def define_ancova_model() -> Dict[str, Any]:
    """
    Define the ANCOVA model configuration.
    
    Returns a dictionary describing the model formula and parameters
    as mandated by the Plan's "Key Methodological Updates".
    
    Formula: time ~ condition + loc + cc + doc_quality
    """
    return {
        "model_type": "ANCOVA",
        "dependent_variable": "task_completion_time",
        "independent_variable": "condition",
        "covariates": [
            {
                "name": "loc",
                "description": "Lines of Code (Repository Complexity)",
                "source": "data/raw/repo_metrics.json (via T021c)"
            },
            {
                "name": "cc",
                "description": "Cyclomatic Complexity (Repository Complexity)",
                "source": "data/raw/repo_metrics.json (via T021c)"
            },
            {
                "name": "doc_quality",
                "description": "Human Documentation Quality Score",
                "source": "data/raw/doc_quality_scores.json (via T021f)"
            }
        ],
        "formula": "task_completion_time ~ C(condition) + loc + cc + doc_quality",
        "library": "statsmodels",
        "methodology_override": "Pre-specified Welch's ANOVA with ANCOVA adjustment",
        "replacement_strategy": "Replaces 'perfect matching' strategy (FR-009) with covariate adjustment"
    }


def generate_strategy_config() -> Dict[str, Any]:
    """
    Generate the full ANCOVA strategy configuration document.
    
    This function:
    1. Loads and validates the covariates.
    2. Defines the model structure.
    3. Compiles statistics about the covariates (counts, ranges).
    
    Returns:
        A dictionary representing the strategy configuration.
    """
    logger.info(f"Loading covariates from {COVARIATES_INPUT_PATH}...")
    covariates_data = load_covariates()
    
    if not validate_covariate_structure(covariates_data):
        raise ValueError("Invalid covariate structure. Cannot proceed with strategy definition.")
    
    logger.info(f"Validated {len(covariates_data)} covariate records.")
    
    # Calculate basic stats for the report
    loc_values = [r['loc'] for r in covariates_data]
    cc_values = [r['cc'] for r in covariates_data]
    doc_q_values = [r['doc_quality'] for r in covariates_data]
    
    stats = {
        "total_repos": len(covariates_data),
        "loc_stats": {
            "min": min(loc_values),
            "max": max(loc_values),
            "mean": sum(loc_values) / len(loc_values)
        },
        "cc_stats": {
            "min": min(cc_values),
            "max": max(cc_values),
            "mean": sum(cc_values) / len(cc_values)
        },
        "doc_quality_stats": {
            "min": min(doc_q_values),
            "max": max(doc_q_values),
            "mean": sum(doc_q_values) / len(doc_q_values)
        }
    }
    
    strategy = {
        "strategy_id": "ancova-primary-fr009",
        "description": "Primary analysis strategy replacing perfect matching with ANCOVA",
        "model_definition": define_ancova_model(),
        "covariate_summary": stats,
        "execution_order": [
            "1. Center covariates (mean-centering) to reduce multicollinearity (T059)",
            "2. Run Welch's ANOVA on task time with condition as factor",
            "3. Run ANCOVA with centered covariates (loc, cc, doc_quality)",
            "4. Report adjusted means and p-values"
        ],
        "dependencies": {
            "covariates_file": str(COVARIATES_INPUT_PATH.relative_to(PROJECT_ROOT)),
            "cleaned_dataset": "data/processed/cleaned_dataset.csv",
            "centered_covariates": "data/processed/centered_covariates.json"
        }
    }
    
    return strategy


def save_strategy_config(strategy: Dict[str, Any]) -> str:
    """
    Save the strategy configuration to the output path.
    
    Args:
        strategy: The strategy configuration dictionary.
        
    Returns:
        The path to the saved file.
    """
    output_dir = OUTPUT_CONFIG_PATH.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(strategy, f, indent=2)
    
    logger.info(f"ANCOVA strategy config saved to {OUTPUT_CONFIG_PATH}")
    return str(OUTPUT_CONFIG_PATH)


def main():
    """
    Entry point for the ANCOVA strategy implementation.
    
    Executes the full pipeline: load -> validate -> define -> save.
    """
    try:
        logger.info("Starting ANCOVA Strategy Implementation (T021h)...")
        strategy = generate_strategy_config()
        output_path = save_strategy_config(strategy)
        logger.info("ANCOVA Strategy Implementation completed successfully.")
        print(f"Output written to: {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
