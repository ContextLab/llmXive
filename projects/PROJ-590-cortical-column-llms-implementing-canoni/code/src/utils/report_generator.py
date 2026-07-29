"""
Report generation utilities for the Cortical Column LLM project.

This module provides functions to generate analysis reports, including
the "cost of biological plausibility" curve derived from ablation studies.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the mapping of ablation flags to constraint names
# These keys correspond to the boolean flags in the ablation configs
CONSTRAINT_MAPPING = {
    'no_recurrence': 'recurrence',
    'no_inhibition': 'inhibition',
    'no_homeostasis': 'homeostasis'
}

def load_ablation_results(filepath: str = "data/results/ablation_results.json") -> List[Dict[str, Any]]:
    """
    Load ablation results from a JSON file.

    Args:
        filepath: Path to the ablation results JSON file.

    Returns:
        List of result dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ablation results file not found: {filepath}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Handle schema variations: {"results": [...]} or direct list
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected ablation results schema: {type(data)}")

def load_ablation_stats(filepath: str = "data/results/ablation_stats.json") -> Optional[Dict[str, Any]]:
    """
    Load ablation statistics from a JSON file.

    Args:
        filepath: Path to the ablation stats JSON file.

    Returns:
        Dictionary of statistics or None if file missing.
    """
    if not os.path.exists(filepath):
        logger.warning(f"Ablation stats file not found: {filepath}")
        return None

    with open(filepath, 'r') as f:
        return json.load(f)

def count_active_constraints(flags: Dict[str, bool]) -> int:
    """
    Count the number of active biological constraints based on ablation flags.

    A constraint is considered 'active' if its corresponding 'no_' flag is False.
    For example, if 'no_recurrence' is False, then 'recurrence' is active.

    Args:
        flags: Dictionary of boolean flags from ablation config.

    Returns:
        Integer count of active constraints.
    """
    count = 0
    for flag_key, constraint_name in CONSTRAINT_MAPPING.items():
        # If the flag exists and is False, the constraint is active
        if flag_key in flags and not flags[flag_key]:
            count += 1
        # If the flag is missing, we assume the constraint is active by default (full model)
        elif flag_key not in flags:
            count += 1
    return count

def generate_cost_curve(ablation_results_path: str = "data/results/ablation_results.json",
                        output_path: str = "data/results/cost_curve.json") -> Dict[str, Any]:
    """
    Generate the "cost of biological plausibility" curve data.

    This function processes ablation study results to create a mapping of
    (number of active constraints) -> (MAE, Time).

    The output JSON schema is:
    {
        "points": [
            {
                "constraints": ["recurrence", "inhibition", "homeostasis"],
                "constraint_count": 3,
                "mae": 0.0123,
                "time": 123.45
            },
            ...
        ],
        "summary": {
            "full_model_mae": float,
            "ablated_min_mae": float,
            "max_cost": float
        }
    }

    Args:
        ablation_results_path: Path to the ablation results JSON.
        output_path: Path where the cost curve JSON will be written.

    Returns:
        The generated cost curve dictionary.

    Raises:
        FileNotFoundError: If ablation results are missing.
        ValueError: If data is inconsistent.
    """
    logger.info(f"Loading ablation results from {ablation_results_path}")
    results = load_ablation_results(ablation_results_path)

    if not results:
        raise ValueError("Ablation results list is empty. Cannot generate cost curve.")

    cost_curve_points = []

    # Process each result
    for result in results:
        variant_name = result.get('variant', 'unknown')
        mae = result.get('mae')
        time_taken = result.get('time')

        if mae is None or time_taken is None:
            logger.warning(f"Skipping result '{variant_name}' due to missing metrics.")
            continue

        # Determine active constraints
        # The result usually comes with the flags used, or we infer from variant name
        # Assuming the result dict contains the flags used for this variant
        flags = result.get('flags', {})

        # If flags are not present in result, try to infer from variant name (fallback)
        if not flags:
            # Heuristic: if variant is 'full', all active. If 'no_recurrence', etc.
            flags = {}
            if 'full' in variant_name.lower():
                flags = {k: False for k in CONSTRAINT_MAPPING.keys()} # All False = all active
            else:
                # Infer from name: 'no_recurrence' -> no_recurrence=True
                for key in CONSTRAINT_MAPPING.keys():
                    if key in variant_name.lower():
                        flags[key] = True
                    else:
                        flags[key] = False

        active_count = count_active_constraints(flags)
        active_constraints_list = [
            CONSTRAINT_MAPPING[k] for k, v in flags.items()
            if not v and k in CONSTRAINT_MAPPING
        ]
        # Add any default constraints if flags were missing (handled in count_active_constraints logic implicitly, but explicit here for list)
        # If flags were missing in result, we assumed full in the fallback, so list should be all
        if not active_constraints_list and flags:
             # This case happens if flags exist but don't match mapping keys exactly
             active_constraints_list = list(CONSTRAINT_MAPPING.values()) # Fallback to all if ambiguous

        point = {
            "constraints": active_constraints_list,
            "constraint_count": active_count,
            "mae": float(mae),
            "time": float(time_taken)
        }
        cost_curve_points.append(point)

    # Sort by constraint count for logical ordering
    cost_curve_points.sort(key=lambda x: x['constraint_count'])

    # Calculate summary stats
    full_model = next((p for p in cost_curve_points if p['constraint_count'] == len(CONSTRAINT_MAPPING)), None)
    ablated_models = [p for p in cost_curve_points if p['constraint_count'] < len(CONSTRAINT_MAPPING)]

    summary = {
        "full_model_mae": full_model['mae'] if full_model else None,
        "ablated_min_mae": min(p['mae'] for p in ablated_models) if ablated_models else None,
        "max_cost": None
    }

    if summary['full_model_mae'] and summary['ablated_min_mae']:
        # Cost is the increase in error (MAE) when adding constraints
        summary['max_cost'] = summary['full_model_mae'] - summary['ablated_min_mae']

    output_data = {
        "points": cost_curve_points,
        "summary": summary
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.info(f"Writing cost curve to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return output_data

def main():
    """
    Main entry point for generating the cost curve report.
    """
    logger.info("Starting cost curve generation...")
    try:
        result = generate_cost_curve()
        logger.info(f"Cost curve generation successful. Summary: {result['summary']}")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Cost curve generation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()