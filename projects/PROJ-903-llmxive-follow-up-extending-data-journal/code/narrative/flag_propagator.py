"""
Flag Propagator Module for llmXive Pipeline.

This module implements T005d: Logic to propagate the "Low Power" flag
from T005b (data validation) into the final story structure and report.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import the specific error defined in T005b
from data.loader import LowPowerError

logger = logging.getLogger(__name__)

def propagate_low_power_flag(
    baseline_output: Dict[str, Any],
    inspector_output: Optional[Dict[str, Any]] = None,
    error_context: Optional[LowPowerError] = None
) -> Dict[str, Any]:
    """
    Propagates the 'Low Power' flag into the final story structure.

    If a LowPowerError is detected (from T005b), this function modifies
    the narrative output to reflect that the analysis could not proceed
    with statistical validity. It ensures the final report contains
    explicit metadata about the failure mode as per FR-006.

    Args:
        baseline_output: The JSON object from the baseline narrative generator.
        inspector_output: Optional JSON object from the counterfactual inspector.
        error_context: The LowPowerError instance if one was caught, None otherwise.

    Returns:
        A modified dictionary representing the final story structure with
        the 'low_power' flag set to True if applicable, and appropriate
        narrative text.
    """
    final_report = {
        "status": "success",
        "low_power_flag": False,
        "n_samples": None,
        "n_numeric": None,
        "narrative": "",
        "baseline": baseline_output,
        "inspector": inspector_output,
        "warnings": []
    }

    if error_context is not None:
        # Extract relevant info from the error if available
        # LowPowerError typically contains n_samples and threshold info
        n_samples = getattr(error_context, 'n_samples', 'unknown')
        threshold = getattr(error_context, 'threshold', 30)
        
        final_report["status"] = "low_power_failure"
        final_report["low_power_flag"] = True
        final_report["n_samples"] = n_samples
        final_report["n_numeric"] = getattr(error_context, 'n_numeric', 0)
        
        # Construct the specific narrative for low power
        # This replaces any generated narrative with the explanation
        narrative_text = (
            f"ANALYSIS HALTED: Insufficient Statistical Power. "
            f"The dataset contains only {n_samples} samples, which is below "
            f"the required threshold of {threshold} (FR-006). "
            "No reliable correlations or counterfactual claims could be generated. "
            "Please select a larger dataset."
        )
        final_report["narrative"] = narrative_text
        final_report["warnings"].append(
            f"Low Power Error: n={n_samples} < {threshold}"
        )
        
        logger.warning(f"Low Power flag propagated. Samples: {n_samples}, Threshold: {threshold}")
    else:
        # Normal path: ensure flags are explicit even if not triggered
        if baseline_output:
            final_report["n_samples"] = baseline_output.get("n_samples")
            final_report["n_numeric"] = baseline_output.get("n_numeric")
            if baseline_output.get("n_samples", 0) < 30:
                # Double check if the error wasn't caught but data is small
                final_report["low_power_flag"] = True
                final_report["status"] = "low_power_warning"
                final_report["narrative"] = (
                    f"WARNING: Statistical power is low (n={baseline_output.get('n_samples')}). "
                    "Results should be interpreted with caution."
                )
            else:
                final_report["narrative"] = baseline_output.get("primary_narrative", "No narrative generated.")
        
        if inspector_output:
            final_report["inspector"] = inspector_output

    return final_report


def write_propagated_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Writes the final propagated report to a JSON file.

    Args:
        report: The dictionary returned by propagate_low_power_flag.
        output_path: The path to write the JSON file (e.g., 'output/final_story.json').
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Propagated report written to {output_file}")


def main():
    """
    CLI entry point for testing the flag propagation logic.
    Simulates a LowPowerError and verifies it propagates to the report.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Simulate a scenario where T005b raised a LowPowerError
    # In a real pipeline, this error would be caught by the main orchestrator
    # and passed here.
    
    dummy_baseline = {
        "r_value": 0.0,
        "p_value": 1.0,
        "var_x": "N/A",
        "var_y": "N/A",
        "significance": "none",
        "primary_narrative": "Analysis could not proceed.",
        "n_samples": 15,
        "n_numeric": 2
    }
    
    # Create a mock LowPowerError to simulate T005b output
    mock_error = LowPowerError(n_samples=15, threshold=30)
    
    print("Testing Low Power Flag Propagation...")
    report = propagate_low_power_flag(
        baseline_output=dummy_baseline,
        inspector_output=None,
        error_context=mock_error
    )
    
    # Verify the flag is set
    assert report["low_power_flag"] is True, "Low power flag should be True"
    assert report["status"] == "low_power_failure", "Status should be low_power_failure"
    assert "Insufficient Statistical Power" in report["narrative"], "Narrative should explain the failure"
    
    # Write to a temporary file to demonstrate artifact creation
    output_path = "output/propagated_story.json"
    write_propagated_report(report, output_path)
    
    print(f"Success. Report written to {output_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
