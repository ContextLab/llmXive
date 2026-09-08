"""
Flag Propagator Module for T005d

Implements logic to propagate the "Low Power" flag from T005b
into the final story structure and report.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from data.loader import LowPowerError
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def propagate_low_power_flag(
    baseline_result: Dict[str, Any],
    inspector_result: Dict[str, Any],
    sample_size: int,
    threshold: int = 30
) -> Dict[str, Any]:
    """
    Propagate the "Low Power" flag into the story structure.

    This function checks if the sample size is below the threshold (n < 30).
    If so, it injects a 'low_power' flag into the narrative structure and
    modifies the validity status of claims to reflect the statistical limitation.

    Args:
        baseline_result: The output dictionary from the baseline analysis (T012).
        inspector_result: The output dictionary from the inspector analysis (T021b).
        sample_size: The number of rows in the processed dataset.
        threshold: The minimum sample size required for statistical power (default 30).

    Returns:
        A modified story structure dictionary with the 'low_power' flag propagated.
    """
    logger.info(f"Checking sample size: n={sample_size}, threshold={threshold}")

    is_low_power = sample_size < threshold
    story_structure = {
        "meta": {
            "sample_size": sample_size,
            "is_low_power": is_low_power,
            "power_threshold": threshold,
            "timestamp": None  # Should be populated by caller if needed
        },
        "baseline_narrative": None,
        "counterfactual_insights": [],
        "summary": ""
    }

    if is_low_power:
        logger.warning(f"Low Power detected (n={sample_size} < {threshold}). Propagating flag.")
        
        # 1. Mark the meta section
        story_structure["meta"]["status"] = "low_power"
        story_structure["meta"]["warning"] = (
            f"Statistical power is low (n={sample_size} < {threshold}). "
            "Correlations may be unstable or spurious. "
            "Counterfactual analysis results are flagged as 'low_power'."
        )

        # 2. Process Baseline Narrative
        if baseline_result:
            # Inject low_power flag into the primary narrative metadata
            baseline_copy = baseline_result.copy()
            baseline_copy["low_power_flag"] = True
            baseline_copy["validity_status"] = "low_power"
            baseline_copy["caution"] = (
                "Results derived from a small sample size (n < 30). "
                "P-values and correlation coefficients should be interpreted with extreme caution."
            )
            story_structure["baseline_narrative"] = baseline_copy
        else:
            story_structure["baseline_narrative"] = {
                "low_power_flag": True,
                "validity_status": "low_power",
                "primary_narrative": "No baseline narrative generated due to low sample size.",
                "caution": "Sample size insufficient for reliable statistical inference."
            }

        # 3. Process Counterfactual Insights
        if inspector_result and isinstance(inspector_result, list):
            # If inspector returned a list of results (e.g., from sensitivity analysis)
            for item in inspector_result:
                item_copy = item.copy()
                item_copy["validity_status"] = "low_power"
                item_copy["stability_score"] = 0.0  # Cannot establish stability with n < 30
                item_copy["caution"] = (
                    "Counterfactual claim validity is compromised by low sample size."
                )
                story_structure["counterfactual_insights"].append(item_copy)
        elif inspector_result and isinstance(inspector_result, dict):
            # If inspector returned a single dict
            inspector_copy = inspector_result.copy()
            inspector_copy["validity_status"] = "low_power"
            inspector_copy["stability_score"] = 0.0
            inspector_copy["caution"] = (
                "Counterfactual claim validity is compromised by low sample size."
            )
            story_structure["counterfactual_insights"].append(inspector_copy)
        else:
            # No inspector result, but low power exists
            story_structure["counterfactual_insights"].append({
                "claim": "No counterfactuals generated due to low sample size.",
                "validity_status": "low_power",
                "stability_score": 0.0,
                "caution": "Sample size insufficient for reliable counterfactual analysis."
            })

        # 4. Generate Summary
        story_structure["summary"] = (
            f"ANALYSIS WARNING: The dataset contains only {sample_size} records, "
            f"which is below the minimum threshold of {threshold} required for robust statistical inference. "
            "All generated narratives and counterfactuals are flagged as 'low_power'. "
            "Results should not be used for decision-making without further validation on a larger dataset."
        )

    else:
        # Normal operation
        logger.info("Sample size is sufficient. Propagating normal status.")
        story_structure["meta"]["status"] = "valid"
        
        if baseline_result:
            baseline_copy = baseline_result.copy()
            baseline_copy["low_power_flag"] = False
            baseline_copy["validity_status"] = baseline_result.get("validity_status", "verified")
            story_structure["baseline_narrative"] = baseline_copy
        
        if inspector_result:
            if isinstance(inspector_result, list):
                story_structure["counterfactual_insights"] = [
                    item.copy() for item in inspector_result
                ]
            elif isinstance(inspector_result, dict):
                story_structure["counterfactual_insights"].append(inspector_result.copy())
        
        story_structure["summary"] = (
            f"Analysis completed on {sample_size} records. "
            "Statistical power is sufficient for standard inference."
        )

    return story_structure


def write_propagated_report(
    story_structure: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write the propagated story structure to a JSON file.

    Args:
        story_structure: The dictionary containing the story with propagated flags.
        output_path: The path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story_structure, f, indent=2, default=str)
    
    logger.info(f"Propagated report written to {output_path}")


def main() -> int:
    """
    Main entry point for the flag propagator script.
    
    This script is intended to be called by the main pipeline (T009) or
    integrated into the narrative stage. For standalone testing, it can
    simulate a scenario where a LowPowerError is caught and the report
    is generated.
    
    Returns:
        0 on success, non-zero on failure.
    """
    config = get_config()
    output_dir = Path(config.get('output_dir', 'output'))
    
    # Simulate inputs for demonstration/standalone run
    # In the real pipeline, these would come from the outputs of T012 and T021b
    # and the sample size from T005b/T006c.
    
    sample_size = 25  # Simulating a low power scenario
    
    mock_baseline = {
        "r_value": 0.45,
        "p_value": 0.02,
        "var_x": "income",
        "var_y": "education",
        "significance": "significant",
        "primary_narrative": "Income is positively correlated with education levels."
    }
    
    mock_inspector = [
        {
            "claim": "Housing price might be the confounder.",
            "p_value": 0.04,
            "partial_r": 0.30,
            "stability_score": 0.6
        }
    ]
    
    try:
        story = propagate_low_power_flag(
            baseline_result=mock_baseline,
            inspector_result=mock_inspector,
            sample_size=sample_size,
            threshold=30
        )
        
        output_file = output_dir / "narrative_with_flags.json"
        write_propagated_report(story, output_file)
        
        print(f"Success: Propagated report generated at {output_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to propagate flags: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())