import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.io_helpers import load_json, write_json
from utils.logging_setup import get_logger

# Constants
SMALL_DATASET_THRESHOLD = 50
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "verified_source_manifest.json"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_JSON_PATH = PROJECT_ROOT / "data" / "processed" / "results.json"
RESEARCH_REPORT_PATH = PROJECT_ROOT / "docs" / "research_results.md"

logger = get_logger(__name__)


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the verified source manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    return load_json(manifest_path)


def extract_subjects_from_raw_files(raw_dir: Path) -> List[str]:
    """
    Extract unique subject IDs from the raw data directory.
    Assumes filenames follow the pattern: sub-{subject_id}_run-{run_id}.edf
    """
    subject_ids = set()
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return []

    for file_path in raw_dir.iterdir():
        if file_path.suffix.lower() == '.edf':
            # Parse filename: sub-{subject_id}_run-{run_id}.edf
            name = file_path.stem
            if name.startswith("sub-") and "_run-" in name:
                try:
                    subject_part = name.split("_run-")[0]
                    subject_id = subject_part.replace("sub-", "")
                    if subject_id:
                        subject_ids.add(subject_id)
                except Exception as e:
                    logger.warning(f"Could not parse subject ID from {file_path.name}: {e}")
    
    return sorted(list(subject_ids))


def analyze_population_demographics(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the manifest to determine population characteristics.
    Returns a dict with flags for 'single_population' and population description.
    """
    # Default assumption: If no specific metadata is found, we flag as potentially single population
    # based on the source search query "EEG AND tDCS AND motor" which often targets healthy adults.
    # In a real scenario, we would parse specific 'population' fields from the manifest.
    
    source_info = manifest.get("sources", [])
    population_notes = []
    is_single_population = True # Conservative default until proven otherwise
    
    for source in source_info:
        dataset_id = source.get("dataset_id", "unknown")
        # Heuristic: If the dataset ID or description doesn't mention diverse populations,
        # or if it's a known small study, flag it.
        # Since we don't have a full DB, we rely on the manifest's "found" status.
        # If the manifest was created by T011 with "Data Insufficient", this function 
        # might not even be called, but if called, we assume a dataset exists.
        
        # Check for keywords that suggest diversity (e.g., "clinical", "patient", "elderly")
        desc = source.get("description", "").lower()
        if any(kw in desc for kw in ["patient", "clinical", "disorder", "elderly", "diverse"]):
            is_single_population = False
            population_notes.append(f"Dataset {dataset_id} suggests diverse/clinical population.")
        else:
            population_notes.append(f"Dataset {dataset_id}: No diversity indicators found; likely healthy young adults.")

    return {
        "is_single_population": is_single_population,
        "population_notes": population_notes,
        "summary": "Dataset likely consists of a single population (e.g., healthy young adults) based on lack of diversity indicators in metadata." if is_single_population else "Dataset shows signs of diverse or clinical populations."
    }


def check_dataset_size(subject_ids: List[str]) -> Dict[str, Any]:
    """
    Check if the dataset size (number of subjects) is below the threshold.
    """
    count = len(subject_ids)
    is_small = count < SMALL_DATASET_THRESHOLD
    return {
        "subject_count": count,
        "threshold": SMALL_DATASET_THRESHOLD,
        "is_small": is_small,
        "message": f"Dataset size ({count} subjects) is below threshold ({SMALL_DATASET_THRESHOLD})." if is_small else f"Dataset size ({count} subjects) meets threshold."
    }


def generate_representativeness_report(
    size_check: Dict[str, Any],
    pop_check: Dict[str, Any],
    manifest: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the final representativeness report dictionary.
    """
    is_representative = not (size_check["is_small"] or pop_check["is_single_population"])
    
    report = {
        "dataset_id": manifest.get("sources", [{}])[0].get("dataset_id", "unknown") if manifest.get("sources") else "unknown",
        "analysis_timestamp": manifest.get("timestamp", "unknown"),
        "size_analysis": size_check,
        "population_analysis": pop_check,
        "flags": {
            "is_small_dataset": size_check["is_small"],
            "is_single_population": pop_check["is_single_population"],
            "is_representative": is_representative
        },
        "summary": f"Dataset {'is NOT representative' if not is_representative else 'is representative'}. " +
                   f"Small dataset: {size_check['is_small']}, Single population: {pop_check['is_single_population']}."
    }
    return report


def update_research_results(report: Dict[str, Any], results_path: Path) -> None:
    """
    Update or create the results.json file with the representativeness flags.
    """
    if results_path.exists():
        try:
            existing_data = load_json(results_path)
        except Exception:
            existing_data = {}
    else:
        existing_data = {}
        results_path.parent.mkdir(parents=True, exist_ok=True)

    existing_data["dataset_representativeness"] = report
    write_json(results_path, existing_data)
    logger.info(f"Updated results at {results_path}")


def update_markdown_report(report: Dict[str, Any], md_path: Path) -> None:
    """
    Update the research_results.md file to include the representativeness check.
    """
    md_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"""# Research Results: Neural Oscillations as a Biomarker for tDCS Response

## Dataset Representativeness Check

**Analysis Date**: {report.get('analysis_timestamp', 'Unknown')}
**Dataset ID**: {report.get('dataset_id', 'Unknown')}

### Summary
{report.get('summary', 'No summary available.')}

### Detailed Findings

#### Dataset Size
- **Subject Count**: {report['size_analysis']['subject_count']}
- **Threshold**: {report['size_analysis']['threshold']}
- **Flag**: {'Small Dataset (< 50 subjects)' if report['flags']['is_small_dataset'] else 'Adequate Size'}
- **Message**: {report['size_analysis']['message']}

#### Population Demographics
- **Single Population Flag**: {'Yes' if report['flags']['is_single_population'] else 'No'}
- **Notes**:
"""
    for note in report['population_analysis'].get('population_notes', []):
        content += f"- {note}\n"
    
    content += f"""
### Conclusion
The dataset is considered {'representative' if report['flags']['is_representative'] else 'NOT representative'} for generalization.
{'WARNING: Results may be limited due to small sample size and/or lack of population diversity.' if not report['flags']['is_representative'] else ''}

---
*Generated by T016: Dataset Representativeness Check*
"""
    
    with open(md_path, 'w') as f:
        f.write(content)
    logger.info(f"Updated markdown report at {md_path}")


def main():
    """
    Main entry point for the Dataset Representativeness Check task.
    """
    logger.info("Starting Dataset Representativeness Check (T016)...")
    
    try:
        # 1. Load Manifest
        manifest = load_manifest(MANIFEST_PATH)
        
        # Check if we have a valid dataset (if manifest indicates failure, we might skip or handle gracefully)
        if manifest.get("mode", "").lower() == "data insufficient":
            logger.warning("Manifest indicates 'Data Insufficient'. Skipping detailed analysis.")
            # Still create a report indicating this state
            report = {
                "dataset_id": "None",
                "analysis_timestamp": "N/A",
                "size_analysis": {"subject_count": 0, "is_small": True, "message": "No data available."},
                "population_analysis": {"is_single_population": True, "population_notes": ["No data available."]},
                "flags": {"is_small_dataset": True, "is_single_population": True, "is_representative": False},
                "summary": "Dataset representativeness check skipped: No data available."
            }
            update_research_results(report, RESULTS_JSON_PATH)
            update_markdown_report(report, RESEARCH_REPORT_PATH)
            return

        # 2. Extract Subjects from Raw Files
        subject_ids = extract_subjects_from_raw_files(RAW_DATA_DIR)
        logger.info(f"Found {len(subject_ids)} unique subjects in raw data.")

        # 3. Analyze Size
        size_check = check_dataset_size(subject_ids)

        # 4. Analyze Population
        pop_check = analyze_population_demographics(manifest)

        # 5. Generate Report
        report = generate_representativeness_report(size_check, pop_check, manifest)

        # 6. Update Outputs
        update_research_results(report, RESULTS_JSON_PATH)
        update_markdown_report(report, RESEARCH_REPORT_PATH)

        logger.info("Dataset Representativeness Check completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during representativeness check: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()