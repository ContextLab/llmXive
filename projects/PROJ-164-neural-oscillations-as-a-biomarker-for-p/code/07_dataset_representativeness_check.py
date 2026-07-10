"""
T016: Dataset Representativeness Check
Analyzes dataset metadata to flag if the dataset is small (<50 subjects) 
or from a single population (e.g., healthy young adults).

Outputs:
- data/processed/representativeness_report.json
- docs/research_results.md (appended with findings)
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_setup import get_logger, log_resource_usage
from utils.io_helpers import load_csv

# Constants from config
MIN_SUBJECTS_THRESHOLD = 50
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the verified source manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def extract_subjects_from_raw_files(raw_dir: Path) -> set:
    """Extract unique subject IDs from raw data files."""
    subjects = set()
    if not raw_dir.exists():
        return subjects
    
    for file_path in raw_dir.iterdir():
        if file_path.suffix.lower() in ['.edf', '.vhdr', '.set', '.fif']:
            # Try to extract subject ID from filename (e.g., sub-001_run-01.edf)
            name = file_path.stem
            if name.startswith('sub-'):
                parts = name.split('_')
                if len(parts) >= 1:
                    subject_id = parts[0].replace('sub-', '')
                    subjects.add(subject_id)
            elif name.startswith('sub_'):
                parts = name.split('_')
                if len(parts) >= 1:
                    subject_id = parts[0].replace('sub_', '')
                    subjects.add(subject_id)
            else:
                # Fallback: use filename as subject ID if pattern not recognized
                subjects.add(name.split('_')[0])
    
    return subjects

def analyze_population_demographics(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze population demographics from manifest metadata.
    Returns flags for potential representativeness issues.
    """
    flags = {
        "is_single_population": False,
        "population_type": "unknown",
        "population_details": []
    }
    
    # Check if manifest has population metadata
    if "metadata" in manifest:
        meta = manifest["metadata"]
        
        # Check for population descriptors
        population_keywords = {
            "healthy": ["healthy", "control", "normal"],
            "young_adult": ["young", "adult", "student", "undergraduate", "graduate"],
            "elderly": ["elderly", "senior", "aged", "older"],
            "clinical": ["patient", "clinical", "disorder", "condition", "disease"],
            "mixed": ["mixed", "diverse", "heterogeneous", "various"]
        }
        
        # Look for population info in various fields
        population_text = ""
        for field in ["description", "population", "subjects", "inclusion_criteria", "exclusion_criteria"]:
            if field in meta:
                if isinstance(meta[field], str):
                    population_text += " " + meta[field].lower()
                elif isinstance(meta[field], list):
                    population_text += " " + " ".join(str(item).lower() for item in meta[field])
        
        # Analyze population text
        detected_categories = []
        for category, keywords in population_keywords.items():
            if any(keyword in population_text for keyword in keywords):
                detected_categories.append(category)
        
        if len(detected_categories) == 1 and "mixed" not in detected_categories:
            flags["is_single_population"] = True
            flags["population_type"] = detected_categories[0]
            flags["population_details"].append(f"Detected single population: {detected_categories[0]}")
        elif len(detected_categories) > 1:
            flags["population_type"] = "mixed"
            flags["population_details"].append(f"Multiple populations detected: {', '.join(detected_categories)}")
        else:
            flags["population_details"].append("No clear population descriptors found in metadata")
    
    # Check source type for potential bias
    source_info = manifest.get("source_info", {})
    source_type = source_info.get("source", "unknown")
    
    if source_type in ["openneuro", "physionet", "kaggle"]:
        if source_type == "openneuro":
            # OpenNeuro often has healthy control studies
            flags["population_details"].append(f"Source: {source_type} (may contain healthy control bias)")
        elif source_type == "physionet":
            flags["population_details"].append(f"Source: {source_type} (clinical focus)")
        elif source_type == "kaggle":
            flags["population_details"].append(f"Source: {source_type} (variable quality)")
    
    return flags

def check_dataset_size(subjects: set, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Check if dataset size meets minimum requirements."""
    n_subjects = len(subjects)
    
    # Also check manifest for explicit subject count
    manifest_count = None
    if "metadata" in manifest and "subject_count" in manifest["metadata"]:
        manifest_count = manifest["metadata"]["subject_count"]
    elif "data_info" in manifest and "n_subjects" in manifest["data_info"]:
        manifest_count = manifest["data_info"]["n_subjects"]
    
    # Use manifest count if available and different from file-based count
    if manifest_count is not None:
        n_subjects = max(n_subjects, manifest_count)
    
    is_underpowered = n_subjects < MIN_SUBJECTS_THRESHOLD
    
    return {
        "n_subjects": n_subjects,
        "threshold": MIN_SUBJECTS_THRESHOLD,
        "is_underpowered": is_underpowered,
        "message": f"Dataset has {n_subjects} subjects (threshold: {MIN_SUBJECTS_THRESHOLD})"
    }

def generate_representativeness_report(
    size_info: Dict[str, Any], 
    population_info: Dict[str, Any],
    manifest_path: Path
) -> Dict[str, Any]:
    """Generate comprehensive representativeness report."""
    report = {
        "task_id": "T016",
        "timestamp": None,  # Will be set by caller if needed
        "manifest_source": str(manifest_path),
        "size_analysis": size_info,
        "population_analysis": population_info,
        "overall_flags": [],
        "recommendations": []
    }
    
    # Determine overall flags
    if size_info["is_underpowered"]:
        report["overall_flags"].append("SMALL_DATASET")
        report["recommendations"].append(
            "Dataset size is below recommended threshold. "
            "Results should be interpreted with caution and may lack generalizability."
        )
    
    if population_info["is_single_population"]:
        report["overall_flags"].append("SINGLE_POPULATION")
        report["recommendations"].append(
            f"Dataset appears to be from a single population ({population_info['population_type']}). "
            "Generalizability to other populations is limited."
        )
    
    if not report["overall_flags"]:
        report["overall_flags"].append("ADEQUATE_REPRESENTATIVENESS")
        report["recommendations"].append(
            "Dataset meets minimum size requirements and shows population diversity."
        )
    
    # Add metadata details
    report["metadata_summary"] = population_info["population_details"]
    
    return report

def update_research_results(report: Dict[str, Any], docs_dir: Path) -> None:
    """Update or create the research results document with representativeness findings."""
    results_file = docs_dir / "research_results.md"
    
    # Ensure docs directory exists
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare the section to add
    section_content = f"""
## Dataset Representativeness Analysis (T016)

### Size Assessment
- **Number of Subjects**: {report['size_analysis']['n_subjects']}
- **Minimum Threshold**: {report['size_analysis']['threshold']}
- **Status**: {'⚠️ Underpowered' if report['size_analysis']['is_underpowered'] else '✅ Adequate'}
- **Details**: {report['size_analysis']['message']}

### Population Diversity
- **Single Population Flag**: {'⚠️ Yes' if report['population_analysis']['is_single_population'] else '✅ No'}
- **Population Type**: {report['population_analysis']['population_type']}
- **Details**:
  {chr(10).join('  - ' + detail for detail in report['metadata_summary'])}

### Overall Assessment
**Flags Detected**: {', '.join(report['overall_flags'])}

### Recommendations
{chr(10).join('- ' + rec for rec in report['recommendations'])}

---
*Analysis generated by T016: Dataset Representativeness Check*
"""
    
    # Read existing content if file exists
    existing_content = ""
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # Check if section already exists to avoid duplicates
    if "## Dataset Representativeness Analysis (T016)" not in existing_content:
        new_content = existing_content + section_content
        with open(results_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    else:
        logging.info("Representativeness section already exists in research_results.md")

def main():
    """Main entry point for T016."""
    logger = get_logger("T016_dataset_representativeness")
    logger.info("Starting Dataset Representativeness Check (T016)")
    
    try:
        # Ensure output directories exist
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load manifest
        manifest_path = PROJECT_ROOT / "data" / "processed" / "verified_source_manifest.json"
        # Fallback to data/raw if not in processed
        if not manifest_path.exists():
            manifest_path = PROJECT_ROOT / "data" / "raw" / "verified_source_manifest.json"
        
        if not manifest_path.exists():
            logger.error("Verified source manifest not found. Cannot perform representativeness check.")
            # Create empty report for downstream tasks
            report = {
                "task_id": "T016",
                "status": "SKIPPED",
                "reason": "Manifest not found",
                "overall_flags": ["MANIFEST_MISSING"]
            }
            report_path = DATA_PROCESSED_DIR / "representativeness_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            return 0
        
        manifest = load_manifest(manifest_path)
        logger.info(f"Loaded manifest from {manifest_path}")
        
        # Extract subjects from raw files
        subjects = extract_subjects_from_raw_files(DATA_RAW_DIR)
        logger.info(f"Found {len(subjects)} unique subjects in raw data")
        
        # Analyze dataset size
        size_info = check_dataset_size(subjects, manifest)
        logger.info(size_info["message"])
        
        # Analyze population demographics
        population_info = analyze_population_demographics(manifest)
        logger.info(f"Population analysis: {population_info['population_type']}")
        
        # Generate comprehensive report
        report = generate_representativeness_report(size_info, population_info, manifest_path)
        
        # Save report to data/processed
        report_path = DATA_PROCESSED_DIR / "representativeness_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved representativeness report to {report_path}")
        
        # Update research results document
        update_research_results(report, DOCS_DIR)
        logger.info("Updated research_results.md with representativeness findings")
        
        # Log resource usage
        log_resource_usage(logger)
        
        logger.info("T016 completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during T016 execution: {str(e)}", exc_info=True)
        # Create error report
        error_report = {
            "task_id": "T016",
            "status": "ERROR",
            "error_message": str(e)
        }
        error_path = DATA_PROCESSED_DIR / "representativeness_report.json"
        with open(error_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        return 1

if __name__ == "__main__":
    sys.exit(main())