"""
Pilot Human Manipulation Check (Task T019)

This script implements the pilot human manipulation check to verify that
salience manipulation preserves the narrative content of images.

It presents manipulated images to a separate coder panel, collects their
judgments on narrative preservation, calculates agreement rates, and
flags scenarios that fail to meet the 0.80 agreement threshold.

Output: data/processed/narrative_check.csv
"""

import os
import sys
import argparse
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Import shared utilities
from config import seed_everything
from logging_config import setup_logging, get_logger
from models import Scenario, StimulusVariant

# Ensure reproducibility
seed_everything(42)

# Constants
AGREEMENT_THRESHOLD = 0.80
MIN_CODERS_REQUIRED = 3
OUTPUT_FILE = "data/processed/narrative_check.csv"

# Setup logging
logger = get_logger(__name__)


class ManipulationCheckError(Exception):
    """Custom exception for manipulation check failures."""
    pass


def load_manipulated_scenarios(input_dir: str = "data/processed") -> List[Dict[str, Any]]:
    """
    Load the list of manipulated scenarios from the previous stage.
    
    This function reads the validated scenarios and their manipulated variants
    to prepare for the human coding check.
    
    Args:
        input_dir: Directory containing processed scenario data.
        
    Returns:
        List of dictionaries containing scenario and variant information.
        
    Raises:
        ManipulationCheckError: If no scenarios are found or data is malformed.
    """
    scenarios_file = Path(input_dir) / "valid_scenarios.csv"
    variants_file = Path(input_dir) / "stimulus_variants.csv"
    
    if not scenarios_file.exists():
        raise ManipulationCheckError(
            f"Required file not found: {scenarios_file}. "
            "Run previous tasks (T015) to generate valid_scenarios.csv."
        )
    
    if not variants_file.exists():
        raise ManipulationCheckError(
            f"Required file not found: {variants_file}. "
            "Run previous tasks (T016) to generate stimulus_variants.csv."
        )
    
    # Load scenarios
    import pandas as pd
    scenarios_df = pd.read_csv(scenarios_file)
    variants_df = pd.read_csv(variants_file)
    
    # Merge to get full context
    merged = pd.merge(
        scenarios_df,
        variants_df,
        on="scenario_id",
        how="inner"
    )
    
    # Filter for manipulated variants only (those with salience_level != 'original')
    manipulated = merged[
        merged["salience_level"].isin(["low", "medium", "high"])
    ]
    
    if len(manipulated) == 0:
        raise ManipulationCheckError(
            "No manipulated variants found. Run T016 to generate salience variants."
        )
    
    logger.info(f"Loaded {len(manipulated)} manipulated variants for checking.")
    return manipulated.to_dict(orient="records")


def collect_coder_annotations(
    scenarios: List[Dict[str, Any]],
    output_csv: str = "data/processed/coder_annotations_raw.csv"
) -> List[Dict[str, Any]]:
    """
    Simulate the collection of coder annotations for narrative preservation.
    
    In a real deployment, this would be a Streamlit app or external survey tool
    where human coders view images and rate narrative preservation.
    
    For this implementation, we simulate the process by:
    1. Checking if an existing annotation file exists (from a previous run)
    2. If not, generating a simulated annotation process that would be
       replaced by real human input in production.
    
    IMPORTANT: This function is designed to FAIL LOUDLY if no real annotations
    are available. In a real pipeline, the user would manually run a survey
    tool to generate the annotations file.
    
    Args:
        scenarios: List of scenario dictionaries to check.
        output_csv: Path to store/load annotations.
        
    Returns:
        List of annotation records.
        
    Raises:
        ManipulationCheckError: If no real annotations are found.
    """
    output_path = Path(output_csv)
    
    # Check if real annotations already exist
    if output_path.exists():
        import pandas as pd
        df = pd.read_csv(output_path)
        logger.info(f"Loaded {len(df)} existing annotations from {output_csv}")
        return df.to_dict(orient="records")
    
    # If no annotations exist, we MUST fail loudly
    # In production, this would be replaced by a call to a real survey tool
    logger.error(
        "No existing annotations found at "
        f"{output_csv}. This task requires REAL human coder annotations. "
        "Please run the survey interface (e.g., code/manipulation_check_ui.py) "
        "to collect annotations, or provide the annotations file manually."
    )
    
    raise ManipulationCheckError(
        "Real human annotations required but not found. "
        "The manipulation check cannot proceed without human coder input. "
        "Please collect annotations using the survey interface or provide "
        "the annotations file at: " + str(output_csv)
    )


def calculate_agreement(
    annotations: List[Dict[str, Any]],
    scenarios: List[Dict[str, Any]]
) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Calculate agreement rates for each scenario.
    
    Agreement is defined as:
    (number of coders agreeing on narrative preservation) / (total coders)
    
    Args:
        annotations: List of annotation records.
        scenarios: List of scenario dictionaries.
        
    Returns:
        Tuple of (agreement_rates, flags) where:
        - agreement_rates: dict mapping scenario_id to agreement rate
        - flags: dict mapping scenario_id to "pass" or "fail"
    """
    import pandas as pd
    
    df = pd.DataFrame(annotations)
    
    # Group by scenario_id
    results = {}
    flags = {}
    
    for scenario_id in df["scenario_id"].unique():
        scenario_annotations = df[df["scenario_id"] == scenario_id]
        
        if len(scenario_annotations) < MIN_CODERS_REQUIRED:
            logger.warning(
                f"Scenario {scenario_id} has only {len(scenario_annotations)} "
                f"coders (minimum required: {MIN_CODERS_REQUIRED}). "
                "Marking as failed due to insufficient data."
            )
            results[scenario_id] = 0.0
            flags[scenario_id] = "fail_insufficient_data"
            continue
        
        # Count agreements on "narrative_preserved" = True
        preserved_count = (scenario_annotations["narrative_preserved"] == True).sum()
        total_cod = len(scenario_annotations)
        
        agreement_rate = preserved_count / total_cod
        results[scenario_id] = agreement_rate
        
        if agreement_rate >= AGREEMENT_THRESHOLD:
            flags[scenario_id] = "pass"
        else:
            flags[scenario_id] = "fail"
    
    return results, flags


def save_results(
    scenarios: List[Dict[str, Any]],
    agreement_rates: Dict[str, float],
    flags: Dict[str, str],
    output_path: str = OUTPUT_FILE
) -> None:
    """
    Save the manipulation check results to a CSV file.
    
    Args:
        scenarios: List of scenario dictionaries.
        agreement_rates: Dict mapping scenario_id to agreement rate.
        flags: Dict mapping scenario_id to pass/fail status.
        output_path: Path to output CSV file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import pandas as pd
    
    results = []
    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        results.append({
            "scenario_id": scenario_id,
            "salience_level": scenario.get("salience_level", "unknown"),
            "agreement_rate": agreement_rates.get(scenario_id, 0.0),
            "status": flags.get(scenario_id, "unknown"),
            "timestamp": datetime.now().isoformat()
        })
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")


def main(args=None):
    """
    Main entry point for the manipulation check pipeline.
    
    Args:
        args: Command line arguments (optional).
    """
    parser = argparse.ArgumentParser(
        description="Pilot Human Manipulation Check (T019)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/processed",
        help="Directory containing processed scenario data"
    )
    parser.add_argument(
        "--annotations-file",
        type=str,
        default="data/processed/coder_annotations_raw.csv",
        help="Path to the coder annotations file"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=OUTPUT_FILE,
        help="Path to output results CSV"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=AGREEMENT_THRESHOLD,
        help="Minimum agreement threshold (default: 0.80)"
    )
    
    parsed_args = parser.parse_args(args)
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        logger.info("Starting Pilot Human Manipulation Check (T019)...")
        
        # Load manipulated scenarios
        scenarios = load_manipulated_scenarios(parsed_args.input_dir)
        logger.info(f"Loaded {len(scenarios)} manipulated scenarios.")
        
        # Collect annotations (this will fail loudly if no real annotations exist)
        annotations = collect_coder_annotations(
            scenarios,
            parsed_args.annotations_file
        )
        logger.info(f"Loaded {len(annotations)} annotations.")
        
        # Calculate agreement
        agreement_rates, flags = calculate_agreement(annotations, scenarios)
        
        # Log summary
        pass_count = sum(1 for f in flags.values() if f == "pass")
        fail_count = sum(1 for f in flags.values() if f.startswith("fail"))
        logger.info(f"Results: {pass_count} passed, {fail_count} failed.")
        
        # Save results
        save_results(scenarios, agreement_rates, flags, parsed_args.output_file)
        
        logger.info("Manipulation check completed successfully.")
        return 0
        
    except ManipulationCheckError as e:
        logger.error(f"Manipulation check failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
