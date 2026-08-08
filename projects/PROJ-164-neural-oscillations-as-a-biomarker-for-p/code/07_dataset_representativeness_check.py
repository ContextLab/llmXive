import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing API surface
from utils.io_helpers import compute_sha256, load_csv
from utils.logging_setup import get_logger

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
MANIFEST_PATH = PROJECT_ROOT / "data" / "verified_source_manifest.json"
RESULTS_JSON_PATH = PROJECT_ROOT / "data" / "processed" / "results.json"
RESEARCH_RESULTS_PATH = DOCS_DIR / "research_results.md"
REPRESENTATIVENESS_REPORT_PATH = DATA_PROCESSED_DIR / "dataset_representativeness.json"

# Thresholds
MIN_SUBJECTS_THRESHOLD = 50

logger = get_logger(__name__)


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the verified source manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)


def extract_subjects_from_raw_files(raw_dir: Path) -> List[str]:
    """
    Extract unique subject IDs from raw data files.
    Assumes files follow pattern sub-{subject_id}_*.edf or similar.
    """
    subjects = set()
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist.")
        return list(subjects)

    for file_path in raw_dir.iterdir():
        if file_path.is_file():
            name = file_path.stem
            # Try to extract subject ID from filename
            # Common patterns: sub-001_run-1.edf, sub-001.edf, 001_run-1.edf
            if name.startswith("sub-"):
                parts = name.split("_")
                if len(parts) >= 1:
                    sub_id = parts[0].replace("sub-", "")
                    subjects.add(sub_id)
            else:
                # Fallback: use the whole name or first part as subject ID
                subjects.add(name.split("_")[0])

    return list(subjects)


def analyze_population_demographics(manifest: Dict[str, Any], subjects: List[str]) -> Dict[str, Any]:
    """
    Analyze dataset metadata to determine population characteristics.
    Returns a dict with demographics flags.
    """
    demographics = {
        "is_single_population": False,
        "population_description": "Unknown",
        "flags": []
    }

    # Check manifest for population info
    source_info = manifest.get("source_info", {})
    dataset_info = source_info.get("dataset", {})
    description = dataset_info.get("description", "")
    keywords = dataset_info.get("keywords", [])

    # Heuristics for single population
    population_keywords = ["healthy", "young", "adults", "students", "control"]
    found_pop_keywords = [kw for kw in population_keywords if kw.lower() in description.lower() or kw.lower() in str(keywords).lower()]

    if len(found_pop_keywords) >= 2:
        demographics["is_single_population"] = True
        demographics["population_description"] = ", ".join(found_pop_keywords)
        demographics["flags"].append("Single population detected (likely healthy young adults)")
    elif "healthy" in description.lower():
        demographics["is_single_population"] = True
        demographics["population_description"] = "Healthy subjects"
        demographics["flags"].append("Single population detected (healthy subjects)")
    elif not found_pop_keywords and len(subjects) < 10:
        # Very small dataset often implies single population
        demographics["is_single_population"] = True
        demographics["population_description"] = "Small sample (likely single population)"
        demographics["flags"].append("Very small dataset, likely single population")

    return demographics


def check_dataset_size(subjects: List[str]) -> Dict[str, Any]:
    """
    Check if the dataset size meets the minimum threshold.
    """
    n_subjects = len(subjects)
    is_small = n_subjects < MIN_SUBJECTS_THRESHOLD

    return {
        "n_subjects": n_subjects,
        "threshold": MIN_SUBJECTS_THRESHOLD,
        "is_small": is_small,
        "flags": ["Dataset is small (<50 subjects)"] if is_small else []
    }


def generate_representativeness_report(
    manifest: Dict[str, Any],
    subjects: List[str],
    size_check: Dict[str, Any],
    demographics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the final representativeness report.
    """
    report = {
        "n_subjects": size_check["n_subjects"],
        "is_small_dataset": size_check["is_small"],
        "is_single_population": demographics["is_single_population"],
        "population_description": demographics["population_description"],
        "flags": size_check["flags"] + demographics["flags"],
        "summary": ""
    }

    # Generate summary
    issues = []
    if size_check["is_small"]:
        issues.append(f"small ({size_check['n_subjects']} subjects)")
    if demographics["is_single_population"]:
        issues.append(f"single population ({demographics['population_description']})")

    if issues:
        report["summary"] = f"Dataset is {', '.join(issues)}. Generalizability may be limited."
        report["recommendation"] = "Interpret results with caution due to limited representativeness."
    else:
        report["summary"] = "Dataset appears representative of the target population."
        report["recommendation"] = "Results may have better generalizability."

    return report


def update_research_results(report: Dict[str, Any], results_json_path: Path, research_results_path: Path) -> None:
    """
    Update results.json and research_results.md with representativeness flags.
    """
    # Ensure directories exist
    results_json_path.parent.mkdir(parents=True, exist_ok=True)
    research_results_path.parent.mkdir(parents=True, exist_ok=True)

    # Load or create results.json
    results_data = {}
    if results_json_path.exists():
        with open(results_json_path, 'r') as f:
            results_data = json.load(f)

    # Update with representativeness data
    results_data["dataset_representativeness"] = report
    results_data["flags"] = results_data.get("flags", []) + report["flags"]

    with open(results_json_path, 'w') as f:
        json.dump(results_data, f, indent=2)

    logger.info(f"Updated {results_json_path} with representativeness flags.")

    # Update research_results.md
    md_content = f"""# Research Results

## Dataset Representativeness

- **Number of Subjects**: {report['n_subjects']}
- **Is Small Dataset (<50)**: {report['is_small_dataset']}
- **Is Single Population**: {report['is_single_population']}
- **Population Description**: {report['population_description']}

### Flags
{chr(10).join(f"- {flag}" for flag in report['flags']) if report['flags'] else "- None"}

### Summary
{report['summary']}

### Recommendation
{report['recommendation']}

---
*Generated by Dataset Representativeness Check (T016)*
"""

    # Append or create
    if research_results_path.exists():
        with open(research_results_path, 'r') as f:
            existing_content = f.read()
        if "## Dataset Representativeness" not in existing_content:
            with open(research_results_path, 'a') as f:
                f.write("\n\n" + md_content)
        else:
            # Replace existing section
            import re
            pattern = r"(## Dataset Representativeness.*?)(?=\n## |\Z)"
            new_content = re.sub(pattern, md_content, existing_content, flags=re.DOTALL)
            with open(research_results_path, 'w') as f:
                f.write(new_content)
    else:
        with open(research_results_path, 'w') as f:
            f.write(md_content)

    logger.info(f"Updated {research_results_path} with representativeness section.")


def main():
    """
    Main entry point for the dataset representativeness check.
    """
    logger.info("Starting Dataset Representativeness Check (T016).")

    try:
        # Load manifest
        manifest = load_manifest(MANIFEST_PATH)
        logger.info(f"Loaded manifest from {MANIFEST_PATH}")

        # Extract subjects from raw files
        subjects = extract_subjects_from_raw_files(DATA_RAW_DIR)
        logger.info(f"Found {len(subjects)} subjects in raw data.")

        # Perform checks
        size_check = check_dataset_size(subjects)
        demographics = analyze_population_demographics(manifest, subjects)

        # Generate report
        report = generate_representativeness_report(manifest, subjects, size_check, demographics)

        # Save report
        REPRESENTATIVENESS_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REPRESENTATIVENESS_REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved representativeness report to {REPRESENTATIVENESS_REPORT_PATH}")

        # Update final outputs
        update_research_results(report, RESULTS_JSON_PATH, RESEARCH_RESULTS_PATH)

        logger.info("Dataset Representativeness Check completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Dataset Representativeness Check failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())