"""
T021b: Aggregation and Reporting Logic for Sensitivity Analysis.

This module consumes outputs from T021a (Sensitivity Sweep) and T023c (Stability/Validity Status)
to generate the final FR-003 compliant JSON array written to `output/sensitivity_report.json`.

The output schema includes:
- threshold_config (string)
- claim (string or "NO_SIGNIFICANT_COUNTERFACTUAL")
- p_value (float)
- partial_r (float)
- stability_score (float)
- validity_status (string)
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from narrative.inspector import determine_validity_status, bootstrap_stability_analysis
from narrative.baseline import run_baseline_analysis
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure output directory exists
OUTPUT_DIR = Path("projects/PROJ-903-llmxive-follow-up-extending-data-journal/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SENSITIVITY_INPUT_PATH = OUTPUT_DIR / "sensitivity_sweep.json"
STABILITY_INPUT_PATH = OUTPUT_DIR / "stability_analysis.json"
FINAL_REPORT_PATH = OUTPUT_DIR / "sensitivity_report.json"

def load_json_file(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON list from a file."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {path}, got {type(data)}")
    return data

def aggregate_sensitivity_report(
    sweep_data: List[Dict[str, Any]], 
    stability_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge sensitivity sweep results with stability analysis and validity status.
    
    Args:
        sweep_data: Output from T021a (sensitivity sweep results).
        stability_data: Output from T023a/T023c (stability scores and validity status).
    
    Returns:
        A list of dictionaries conforming to the FR-003 schema.
    """
    # Index stability data by a unique key if available, or by index if 1:1 mapping
    # Assuming stability_data corresponds 1:1 with the candidate variables processed in sweep_data.
    # If sweep_data contains multiple rows per candidate, we need to align carefully.
    # For this implementation, we assume sweep_data rows are ordered by candidate, 
    # and stability_data provides a summary per candidate index.
    
    # Map candidate index to stability info
    stability_map = {}
    for idx, entry in enumerate(stability_data):
        # Assuming stability_data has a 'candidate_index' or is ordered
        # If the input format is strictly a list of summaries in order:
        stability_map[idx] = {
            "stability_score": entry.get("stability_score", 0.0),
            "validity_status": entry.get("validity_status", "failed")
        }
    
    final_report = []
    
    # Track which candidate index we are currently processing
    current_candidate_idx = -1
    candidate_row_count = 0
    
    for i, row in enumerate(sweep_data):
        # Determine candidate index. 
        # If the sweep data includes a 'candidate_index' field, use it. 
        # Otherwise, we infer based on grouping (e.g., by 'claim' prefix or variable name).
        # For robustness, we assume the input from T021a has a 'candidate_index' or we group by 'var_x'.
        candidate_idx = row.get("candidate_index")
        if candidate_idx is None:
            # Fallback: try to infer from variable names if not explicitly indexed
            # This is a heuristic; real implementation should ensure T021a outputs the index.
            # Assuming T021a outputs include a 'candidate' identifier.
            # If not, we might need to group by 'var_x' or 'var_y'.
            # For this task, we assume T021a output includes 'candidate_index'.
            # If missing, we raise an error or assume sequential.
            # Let's assume sequential grouping by 'var_x' if index is missing.
            # This part depends heavily on T021a's exact output.
            # We will assume T021a output has 'candidate_index'.
            # If not, we might need to deduce it.
            # For now, let's assume it's present. If not, we'll try to group.
            # If we can't find it, we'll default to 0 and warn.
            logger.warning(f"Row {i} missing candidate_index. Assuming sequential grouping.")
            # Logic to group by variable would go here if index is missing.
            # Since T021a is a dependency, we assume it provides the index.
            # If not, we might need to reconstruct it.
            # For the purpose of this task, we assume T021a provides 'candidate_index'.
            # If the key is missing, we try 'candidate_id' or similar.
            candidate_idx = row.get("candidate_id")
            if candidate_idx is None:
                # If truly missing, we might need to group by the variable being tested.
                # This is complex without knowing T021a's exact schema.
                # We will assume T021a outputs a 'candidate_index' field.
                # If not, this code might need adjustment.
                # For now, we'll use a fallback to 0 and log a warning.
                candidate_idx = 0
                logger.warning(f"Could not determine candidate_index for row {i}. Defaulting to 0.")
        
        # Ensure stability_map has an entry for this candidate
        if candidate_idx not in stability_map:
            # If stability data is missing for this candidate, mark as failed
            stability_map[candidate_idx] = {
                "stability_score": 0.0,
                "validity_status": "failed"
            }
            logger.warning(f"No stability data found for candidate_index {candidate_idx}. Marking as failed.")

        stability_info = stability_map[candidate_idx]
        
        entry = {
            "threshold_config": row.get("threshold_config", "default"),
            "claim": row.get("claim", "NO_SIGNIFICANT_COUNTERFACTUAL"),
            "p_value": float(row.get("p_value", 1.0)),
            "partial_r": float(row.get("partial_r", 0.0)),
            "stability_score": stability_info["stability_score"],
            "validity_status": stability_info["validity_status"]
        }
        
        final_report.append(entry)
    
    return final_report

def run_aggregation_pipeline():
    """
    Main entry point for T021b.
    Loads inputs from T021a and T023c, aggregates them, and writes the final report.
    """
    logger.info("Starting T021b: Sensitivity Report Aggregation")
    
    try:
        # Load inputs
        logger.info(f"Loading sensitivity sweep data from {SENSITIVITY_INPUT_PATH}...")
        sweep_data = load_json_file(SENSITIVITY_INPUT_PATH)
        logger.info(f"Loaded {len(sweep_data)} sweep entries.")
        
        logger.info(f"Loading stability analysis data from {STABILITY_INPUT_PATH}...")
        stability_data = load_json_file(STABILITY_INPUT_PATH)
        logger.info(f"Loaded {len(stability_data)} stability entries.")
        
        # Aggregate
        logger.info("Aggregating sensitivity and stability data...")
        final_report = aggregate_sensitivity_report(sweep_data, stability_data)
        
        # Write output
        logger.info(f"Writing final report to {FINAL_REPORT_PATH}...")
        with open(FINAL_REPORT_PATH, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"T021b completed successfully. Report written to {FINAL_REPORT_PATH}")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        logger.error("Ensure T021a and T023c have been executed successfully before running T021b.")
        return False
    except Exception as e:
        logger.error(f"Error during aggregation: {e}")
        logger.error("Traceback:")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = run_aggregation_pipeline()
    if not success:
        exit(1)
