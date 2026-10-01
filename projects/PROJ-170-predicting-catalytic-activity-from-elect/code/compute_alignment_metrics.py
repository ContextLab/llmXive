import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger

def load_unified_dataframe() -> Optional[Dict[str, Any]]:
    """
    Load the unified dataframe from the processed data file.
    Since we don't have a pandas dependency in this specific file's context,
    we load the CSV as a dictionary representation or use pandas if available.
    Given the pipeline context, we assume pandas is available.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required to load the unified dataframe")

    data_path = get_data_path()
    input_file = data_path / "processed" / "aligned_dataset.csv"

    if not input_file.exists():
        logger = get_logger(__name__)
        logger.error(f"Unified dataset file not found: {input_file}")
        return None

    df = pd.read_csv(input_file)
    return df

def compute_alignment_success_rate(df) -> Dict[str, Any]:
    """
    Calculate the alignment success rate (SC-002).
    Rate = (matched entries / total entries in the active experimental dataset).
    In this context, the 'active' dataset is the OC20 sample we processed.
    The 'matched' entries are those that successfully made it into the final
    aligned dataset (after filtering for NaN targets, etc.).
    However, the task description implies comparing against the total available
    in the source (OC20) vs what was aligned.
    
    Since T013b generates the unified dataframe with entry_ids, and T017a/T020
    filter out invalid entries, the 'total entries' for the denominator should
    be the count of entries in the *source* OC20 sample that were attempted.
    
    Wait, the task says: "Calculate (matched entries / total entries in the *active* experimental dataset, i.e., OC20)".
    If we only have the final aligned dataset, we might not know the original total count
    unless it was logged or stored.
    
    Assumption: The 'aligned_dataset.csv' contains ONLY the successfully aligned entries.
    We need the original count. If not available in metadata, we might need to infer
    or assume the task implies: (Rows in aligned_dataset) / (Total rows in aligned_dataset + Excluded).
    
    However, looking at T017a, it says "save list of flagged entries to outputs/excluded_entries.json".
    Let's try to load that if it exists to get the excluded count.
    
    If excluded_entries.json doesn't exist or is empty, we might have to assume
    the 'total' is the current count (100% success) or fail.
    
    Better approach for this specific task T013:
    The 'active' dataset is the OC20 sample.
    The 'matched' entries are those in `aligned_dataset.csv`.
    The 'total' entries are those in `aligned_dataset.csv` + `excluded_entries.json` (if any).
    If we don't have the excluded list, we can't calculate the rate accurately against the source.
    
    However, often in these pipelines, the 'total' is the count of rows in the raw file.
    Let's assume the pipeline logic ensures we can derive this.
    If `excluded_entries.json` is missing, we will assume the current dataset is the result
    of the alignment process and calculate based on available metadata.
    
    Actually, re-reading T013: "Calculate (matched entries / total entries in the *active* experimental dataset)".
    If the active dataset is OC20, and we downloaded a stratified sample, the 'total' is the size of that sample.
    Let's check if we can get the size of the sample from the raw file or metadata.
    
    Alternative interpretation: The task might just want the ratio of valid rows in the final CSV
    relative to the input to the alignment step.
    
    Let's implement a robust calculation:
    1. Count rows in `aligned_dataset.csv` (matched).
    2. Try to load `excluded_entries.json` to count excluded.
    3. Total = matched + excluded.
    4. If excluded is missing, we might need to load the raw sample count.
    
    Since T017a produces `excluded_entries.json`, we rely on it.
    If it doesn't exist, we assume no exclusions (Total = Matched).
    """
    import pandas as pd

    matched_count = len(df)
    
    excluded_count = 0
    excluded_file = get_output_path() / "excluded_entries.json"
    if excluded_file.exists():
        try:
            with open(excluded_file, 'r') as f:
                excluded_data = json.load(f)
                # The file might be a list of IDs or a dict with a count
                if isinstance(excluded_data, list):
                    excluded_count = len(excluded_data)
                elif isinstance(excluded_data, dict) and 'excluded_entries' in excluded_data:
                    excluded_count = len(excluded_data['excluded_entries'])
                elif isinstance(excluded_data, dict) and 'count' in excluded_data:
                    excluded_count = excluded_data['count']
        except (json.JSONDecodeError, KeyError):
            logger = get_logger(__name__)
            logger.warning(f"Could not parse excluded_entries.json, assuming 0 excluded.")

    total_entries = matched_count + excluded_count

    if total_entries == 0:
        success_rate = 0.0
    else:
        success_rate = matched_count / total_entries

    return {
        "matched_entries": matched_count,
        "excluded_entries": excluded_count,
        "total_entries": total_entries,
        "alignment_success_rate": success_rate
    }

def save_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save the alignment metrics to a JSON file.
    """
    if output_path is None:
        output_path = get_output_path()
    
    output_file = output_path / "alignment_metrics.json"
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger = get_logger(__name__)
    logger.info(f"Alignment metrics saved to {output_file}")

def main():
    """
    Main entry point for computing alignment metrics.
    """
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting alignment metrics computation (T013)")

    # Load the unified dataframe
    df = load_unified_dataframe()
    if df is None:
        logger.error("Failed to load unified dataframe. Aborting.")
        sys.exit(1)

    # Compute metrics
    metrics = compute_alignment_success_rate(df)
    
    # Log the rate explicitly as requested
    logger.info(f"Alignment Success Rate: {metrics['alignment_success_rate']:.4f} "
                f"({metrics['matched_entries']}/{metrics['total_entries']})")

    # Save metrics
    save_metrics(metrics)

    logger.info("Alignment metrics computation completed.")

if __name__ == "__main__":
    main()