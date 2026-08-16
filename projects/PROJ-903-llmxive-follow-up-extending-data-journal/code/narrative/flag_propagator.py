"""
Flag Propagator Module for llmXive Pipeline.

This module implements the logic to propagate the "Low Power" flag from
the data loading stage (T005b) into the final story structure and reports.
It ensures that datasets failing the sample size check (n < 30) are explicitly
marked in the narrative output and the final aggregation report.
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
    narrative_input: Optional[Dict[str, Any]],
    dataset_id: str,
    error_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Propagates the Low Power flag into the narrative structure.

    If the input narrative is None or indicates a failure due to LowPowerError,
    this function constructs a standard "Low Power" narrative object that
    adheres to the project's schema requirements for edge cases.

    Args:
        narrative_input: The output from the baseline narrative generator.
                         If None or if it contains a 'low_power' flag, it is overridden.
        dataset_id: The unique identifier for the dataset being processed.
        error_context: Optional dictionary containing details about the error
                       (e.g., sample size detected, threshold).

    Returns:
        A dictionary representing the narrative output, guaranteed to contain
        the 'low_power' flag if applicable.
    """
    config = get_config()
    result = {
        "dataset_id": dataset_id,
        "status": "completed",
        "narrative": None,
        "flags": [],
        "warnings": []
    }

    # Check if we need to force the Low Power flag
    # This happens if narrative_input is None (pipeline halted early)
    # or if the input explicitly signals a low power condition
    is_low_power = False
    if narrative_input is None:
        is_low_power = True
        logger.warning(f"Dataset {dataset_id}: Narrative input is None. Assuming Low Power condition.")
    elif isinstance(narrative_input, dict) and narrative_input.get("status") == "low_power":
        is_low_power = True
        logger.info(f"Dataset {dataset_id}: Narrative input explicitly flagged as Low Power.")
    elif isinstance(narrative_input, dict) and narrative_input.get("flags") and "low_power" in narrative_input.get("flags", []):
        is_low_power = True
        logger.info(f"Dataset {dataset_id}: Narrative input contains 'low_power' flag.")

    if is_low_power:
        result["status"] = "low_power"
        result["flags"].append("low_power")
        
        # Construct the standard Low Power narrative message
        sample_size = error_context.get("sample_size") if error_context else "unknown"
        min_required = config.min_sample_size if hasattr(config, 'min_sample_size') else 30
        
        narrative_text = (
            f"Analysis halted for dataset '{dataset_id}'. "
            f"Insufficient statistical power detected: sample size (n={sample_size}) "
            f"is below the required threshold (n >= {min_required}). "
            "No primary narrative or counterfactual analysis could be generated."
        )
        
        result["narrative"] = {
            "primary_narrative": narrative_text,
            "r_value": None,
            "p_value": None,
            "var_x": None,
            "var_y": None,
            "significance": "insufficient_data",
            "edge_case_reason": "low_power"
        }
        
        result["warnings"].append(
            f"Low Power Error: n={sample_size} < {min_required}. "
            "Dataset excluded from correlation analysis."
        )
    else:
        # Normal flow: merge input narrative but ensure flags are preserved
        if narrative_input:
            result["narrative"] = narrative_input.get("narrative") or narrative_input
            result["flags"] = narrative_input.get("flags", [])
            result["warnings"] = narrative_input.get("warnings", [])
            
            # Ensure status reflects success if no low power flag
            if "low_power" not in result["flags"]:
                result["status"] = "completed"

    return result


def write_propagated_report(
    reports: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Writes the list of propagated narrative reports to a JSON file.

    This function aggregates the results from multiple datasets, ensuring
    that any "Low Power" flags are clearly visible in the final report.

    Args:
        reports: List of narrative dictionaries returned by propagate_low_power_flag.
        output_path: Path to the output JSON file (e.g., output/narrative_report.json).
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    report_summary = {
        "total_datasets": len(reports),
        "low_power_count": sum(1 for r in reports if r.get("status") == "low_power"),
        "completed_count": sum(1 for r in reports if r.get("status") == "completed"),
        "reports": reports
    }

    logger.info(f"Writing propagated report to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_summary, f, indent=2, default=str)

    logger.info(f"Report written. Low Power cases: {report_summary['low_power_count']}")


def main() -> None:
    """
    Entry point for the flag propagator script.
    
    This script is designed to be called by the main pipeline (T009) after
    the narrative stage. It reads the raw narrative outputs (or errors)
    and ensures the Low Power flag is correctly propagated to the final JSON.
    
    Usage:
        python code/narrative/flag_propagator.py --input <input_json> --output <output_json>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Propagate Low Power flags to narrative reports.")
    parser.add_argument("--input", type=str, required=True, help="Path to the raw narrative JSON or list of errors.")
    parser.add_argument("--output", type=str, required=True, help="Path to the final propagated report JSON.")
    parser.add_argument("--dataset", type=str, default="unknown", help="Dataset ID if processing a single item.")
    
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        # If input is missing, it might be because the pipeline halted early due to LowPowerError
        # We create a synthetic entry for the specific dataset ID provided
        logger.warning(f"Creating Low Power entry for dataset: {args.dataset}")
        reports = [
            propagate_low_power_flag(
                narrative_input=None,
                dataset_id=args.dataset,
                error_context={"sample_size": "0", "reason": "File not found (likely halted early)"}
            )
        ]
    else:
        with open(input_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in input file: {input_path}")
                return

        if isinstance(data, list):
            # Batch processing
            reports = []
            for item in data:
                # Handle list of dicts where each might have dataset_id and narrative/error
                  rid = item.get("dataset_id", item.get("id", "unknown"))
                  narrative = item.get("narrative")
                  error = item.get("error")
                  
                  context = None
                  if error:
                      if "LowPowerError" in str(error):
                          context = {"sample_size": error.get("sample_size", "unknown")}
                  
                  reports.append(propagate_low_power_flag(narrative, rid, context))
        elif isinstance(data, dict):
            # Single item processing
            rid = data.get("dataset_id", args.dataset)
            narrative = data.get("narrative")
            error = data.get("error")
            context = None
            if error and "LowPowerError" in str(error):
                context = {"sample_size": error.get("sample_size", "unknown")}
            
            reports = [propagate_low_power_flag(narrative, rid, context)]
        else:
            logger.error(f"Unexpected input format: {type(data)}")
            return

    write_propagated_report(reports, output_path)


if __name__ == "__main__":
    main()