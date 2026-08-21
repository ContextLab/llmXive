"""
Report generation module for data unavailability scenarios.

This module is triggered when T012 (load_raw_text_corpus) fails to find
a required column (human_intensity_score) in the dataset. It generates a
formal scientific report documenting the failure and halting the pipeline.
"""

import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import yaml

from src.utils.io import ensure_directory, set_global_seed


def generate_data_unavailable_report(
    dataset_id: str,
    missing_columns: List[str],
    attempted_sources: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    seed: int = 42
) -> dict:
    """
    Generate a formal "Data Unavailable" report when required data is missing.

    This function creates a markdown report and a YAML summary detailing the
    specific dataset checked, the missing modalities (columns), and the
    reason for halting the pipeline.

    Args:
        dataset_id: The identifier of the dataset that was checked (e.g., 'cmu/text_messages_v1').
        missing_columns: List of required columns that were not found (e.g., ['human_intensity_score']).
        attempted_sources: Optional list of other sources that were attempted.
        output_dir: Directory to write the report. Defaults to 'data/reports'.
        seed: Random seed for reproducibility (set globally).

    Returns:
        A dictionary containing the report metadata and file paths.
    """
    # Set global seed for reproducibility
    set_global_seed(seed)

    # Ensure output directory exists
    if output_dir is None:
        output_dir = "data/reports"
    
    output_path = Path(output_dir)
    ensure_directory(output_path)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_filename = f"data_unavailable_report_{timestamp.replace(' ', '_').replace(':', '-')}.md"
    yaml_filename = f"data_unavailable_summary_{timestamp.replace(' ', '_').replace(':', '-')}.yaml"

    report_path = output_path / report_filename
    yaml_path = output_path / yaml_filename

    # Construct the report content
    report_content = f"""# Data Unavailable Report

**Generated:** {timestamp}
**Status:** PIPELINE HALTED

## Summary
The automated data ingestion pipeline has been halted due to the unavailability of
critical required data modalities. The dataset checked did not contain the necessary
columns to proceed with the analysis of emoji influence on perceived emotional intensity.

## Dataset Information
- **Dataset ID:** `{dataset_id}`
- **Attempted Sources:** {', '.join(attempted_sources) if attempted_sources else 'Primary source only'}

## Missing Modalities
The following required columns were not found in the dataset:
{chr(10).join(f'- `{col}`' for col in missing_columns)}

## Impact on Analysis
The absence of `{', '.join(missing_columns)}` prevents the execution of the following
user stories and analysis steps:
- **US1 (Data Ingestion):** Cannot validate message intensity scores.
- **US2 (Power Analysis Verification):** Cannot verify sample size sufficiency against intensity metrics.
- **US3 (Statistical Analysis):** Cannot compute correlation or regression models involving intensity.

## Next Steps
1. **Verify Dataset:** Confirm if the dataset ID `{dataset_id}` is correct and up-to-date.
2. **Alternative Source:** Consult the `data-model.md` and `research.md` for alternative
   public datasets that include `{', '.join(missing_columns)}`.
3. **Manual Intervention:** If this dataset is known to be incomplete, update the
   loader configuration in `src/data/loaders.py` to skip or flag this dataset.

## Technical Details
- **Error Type:** DataUnavailableError
- **Pipeline Version:** 1.0.0 (MVP)
- **Seed Used:** {seed}
"""

    # Write Markdown Report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    # Create YAML Summary for programmatic consumption
    summary_data = {
        "status": "HALTED",
        "timestamp": timestamp,
        "dataset_id": dataset_id,
        "missing_columns": missing_columns,
        "attempted_sources": attempted_sources or [],
        "report_file": str(report_path),
        "reason": f"Missing required columns: {', '.join(missing_columns)}"
    }

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(summary_data, f, default_flow_style=False, sort_keys=False)

    return {
        "status": "report_generated",
        "markdown_file": str(report_path),
        "yaml_file": str(yaml_path),
        "summary": summary_data
    }

def main():
    """
    Entry point for testing the report generation script independently.
    Simulates a failure scenario where 'human_intensity_score' is missing.
    """
    print("Generating Data Unavailable Report (Simulation)...")
    
    result = generate_data_unavailable_report(
        dataset_id="cmu/text_messages_v1",
        missing_columns=["human_intensity_score"],
        attempted_sources=["huggingface", "kaggle_mirror"]
    )
    
    print(f"Report generated successfully.")
    print(f"Markdown: {result['markdown_file']}")
    print(f"YAML: {result['yaml_file']}")
    
    # Verify files exist
    if os.path.exists(result['markdown_file']) and os.path.exists(result['yaml_file']):
        print("Verification: Files written to disk.")
        return 0
    else:
        print("Verification: Failed to write files.")
        return 1

if __name__ == "__main__":
    exit(main())