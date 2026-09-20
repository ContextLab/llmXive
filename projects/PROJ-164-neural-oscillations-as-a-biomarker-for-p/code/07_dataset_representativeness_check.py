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
PROJECT_ID = "PROJ-164-neural-oscillations-as-a-biomarker-for-p"
MANIFEST_PATH = Path("verified_source_manifest.json")
RAW_DATA_DIR = Path("data/raw")
RESULTS_PATH = Path("docs/research_results.md")
RESULTS_JSON_PATH = Path("data/processed/results.json")

logger = get_logger(__name__)

def load_manifest(manifest_path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    """Load the verified source manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    return load_json(manifest_path)

def extract_subjects_from_raw_files(raw_dir: Path = RAW_DATA_DIR) -> List[str]:
    """
    Extract unique subject IDs from raw data files.
    Expected pattern: sub-{subject_id}_run-{run_id}.edf
    """
    subjects = set()
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist.")
        return list(subjects)

    for file_path in raw_dir.glob("sub-*_run-*.edf"):
        # Extract subject ID from filename
        # Format: sub-{subject_id}_run-{run_id}.edf
        parts = file_path.stem.split("_")
        if len(parts) >= 2 and parts[0].startswith("sub-"):
            subject_id = parts[0][4:]  # Remove 'sub-' prefix
            subjects.add(subject_id)

    logger.info(f"Found {len(subjects)} unique subjects in {raw_dir}")
    return sorted(list(subjects))

def analyze_population_demographics(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze dataset metadata to determine population demographics.
    Returns a dictionary with population characteristics.
    """
    population_info = {
        "is_single_population": False,
        "population_description": "Unknown",
        "demographics_flags": []
    }

    # Check manifest for population metadata
    if "metadata" in manifest:
        meta = manifest["metadata"]
        
        # Check for population descriptors
        population_terms = ["healthy", "young", "adults", "elderly", "patients", 
                          "control", "clinical", "healthy young adults"]
        
        description = meta.get("description", "").lower()
        source = meta.get("source", "").lower()
        
        # Analyze description
        single_pop_terms = []
        for term in population_terms:
            if term in description:
                single_pop_terms.append(term)
        
        if len(single_pop_terms) >= 2:
            # Likely a single population
            population_info["is_single_population"] = True
            population_info["population_description"] = " ".join(single_pop_terms)
            population_info["demographics_flags"].append("Single population detected")
        
        # Check for specific demographics
        if "healthy young adults" in description:
            population_info["population_description"] = "Healthy young adults"
            population_info["demographics_flags"].append("Restricted to healthy young adults")
        elif "patients" in description or "clinical" in description:
            population_info["population_description"] = "Clinical population"
            population_info["demographics_flags"].append("Clinical/patient population")
        elif "elderly" in description:
            population_info["population_description"] = "Elderly population"
            population_info["demographics_flags"].append("Elderly population")
        
        # Check source for population hints
        if "openneuro" in source or "physionet" in source:
            # Check if there's specific population info
            if "population" in meta:
                population_info["population_description"] = meta["population"]

    return population_info

def check_dataset_size(subjects: List[str]) -> Dict[str, Any]:
    """
    Check if dataset size meets minimum requirements.
    Returns size analysis results.
    """
    n_subjects = len(subjects)
    
    size_info = {
        "n_subjects": n_subjects,
        "is_small_dataset": n_subjects < SMALL_DATASET_THRESHOLD,
        "threshold": SMALL_DATASET_THRESHOLD,
        "flags": []
    }
    
    if n_subjects < SMALL_DATASET_THRESHOLD:
        size_info["flags"].append(f"Small dataset: {n_subjects} subjects (threshold: {SMALL_DATASET_THRESHOLD})")
        logger.warning(f"Dataset is small: {n_subjects} subjects")
    else:
        logger.info(f"Dataset size is adequate: {n_subjects} subjects")
    
    return size_info

def generate_representativeness_report(
    size_analysis: Dict[str, Any],
    population_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a comprehensive representativeness report.
    """
    report = {
        "dataset_size": size_analysis,
        "population_demographics": population_analysis,
        "representativeness_flags": [],
        "summary": ""
    }
    
    # Combine flags
    report["representativeness_flags"].extend(size_analysis["flags"])
    report["representativeness_flags"].extend(population_analysis["demographics_flags"])
    
    # Generate summary
    issues = []
    if size_analysis["is_small_dataset"]:
        issues.append(f"Small sample size ({size_analysis['n_subjects']} < {SMALL_DATASET_THRESHOLD})")
    
    if population_analysis["is_single_population"]:
        issues.append(f"Single population: {population_analysis['population_description']}")
    
    if issues:
        report["summary"] = "Dataset has limited representativeness: " + "; ".join(issues)
        report["is_representative"] = False
    else:
        report["summary"] = "Dataset appears reasonably representative"
        report["is_representative"] = True
    
    return report

def update_research_results(
    report: Dict[str, Any],
    results_json_path: Path = RESULTS_JSON_PATH,
    results_md_path: Path = RESULTS_PATH
):
    """
    Update research results with representativeness check findings.
    Creates or updates results.json and docs/research_results.md
    """
    # Ensure data/processed directory exists
    results_json_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing results if present
    if results_json_path.exists():
        existing_results = load_json(results_json_path)
    else:
        existing_results = {}
    
    # Update with representativeness data
    existing_results["dataset_representativeness"] = report
    existing_results["representativeness_flags"] = report["representativeness_flags"]
    existing_results["is_representative"] = report["is_representative"]
    
    # Write updated results
    write_json(results_json_path, existing_results)
    logger.info(f"Updated representativeness data in {results_json_path}")
    
    # Update markdown report
    update_markdown_report(report, results_md_path)

def update_markdown_report(report: Dict[str, Any], md_path: Path):
    """
    Update the research results markdown file with representativeness findings.
    """
    md_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create or load existing content
    if md_path.exists():
        content = md_path.read_text()
    else:
        content = "# Research Results\n\n"
    
    # Find or create the representativeness section
    section_marker = "## Dataset Representativeness"
    
    # Generate section content
    section_content = f"""{section_marker}

**Representativeness Assessment**: {'Limited' if not report['is_representative'] else 'Adequate'}

### Dataset Size
- **Number of Subjects**: {report['dataset_size']['n_subjects']}
- **Threshold**: {report['dataset_size']['threshold']}
- **Is Small Dataset**: {report['dataset_size']['is_small_dataset']}

### Population Demographics
- **Population Description**: {report['population_demographics']['population_description']}
- **Single Population**: {report['population_demographics']['is_single_population']}

### Flags
"""
    
    for flag in report["representativeness_flags"]:
        section_content += f"- {flag}\n"
    
    section_content += f"\n### Summary\n{report['summary']}\n"
    
    # Insert or update the section
    if section_marker in content:
        # Find the start of the section
        start_idx = content.find(section_marker)
        # Find the start of the next section (if any)
        next_section_idx = content.find("## ", start_idx + len(section_marker))
        
        if next_section_idx == -1:
            # No next section, append to end
            content = content[:start_idx] + section_content
        else:
            # Replace existing section
            content = content[:start_idx] + section_content + content[next_section_idx:]
    else:
        # Append new section
        content += "\n" + section_content
    
    # Write updated content
    md_path.write_text(content)
    logger.info(f"Updated research results in {md_path}")

def main():
    """
    Main function to perform dataset representativeness check.
    """
    logger.info("Starting dataset representativeness check (T016)")
    
    try:
        # Load manifest
        manifest = load_manifest()
        logger.info("Loaded verified source manifest")
        
        # Extract subjects from raw files
        subjects = extract_subjects_from_raw_files()
        logger.info(f"Extracted {len(subjects)} subjects from raw data")
        
        if not subjects:
            logger.warning("No subjects found in raw data directory")
            report = {
                "dataset_size": {"n_subjects": 0, "is_small_dataset": True, "threshold": SMALL_DATASET_THRESHOLD, "flags": ["No subjects found"]},
                "population_demographics": {"is_single_population": False, "population_description": "Unknown", "demographics_flags": []},
                "representativeness_flags": ["No subjects found"],
                "is_representative": False,
                "summary": "Cannot assess representativeness: no subjects found"
            }
        else:
            # Analyze dataset size
            size_analysis = check_dataset_size(subjects)
            
            # Analyze population demographics
            population_analysis = analyze_population_demographics(manifest)
            
            # Generate report
            report = generate_representativeness_report(size_analysis, population_analysis)
        
        # Update research results
        update_research_results(report)
        
        logger.info("Dataset representativeness check completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Dataset representativeness check failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())