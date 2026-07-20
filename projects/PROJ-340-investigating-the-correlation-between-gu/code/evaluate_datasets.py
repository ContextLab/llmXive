"""
Dataset Evaluation Module for US5 (Data Availability & Source Verification).

This module implements the evaluation of identified datasets for data quality,
variable completeness, and privacy constraints as per Task T050.
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional

# Constants for output paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
EVALUATION_MATRIX_PATH = DATA_METADATA_DIR / "dataset_evaluation_matrix.csv"

# Required variables for the gut-microbiome-sleep study (from specs)
REQUIRED_MICROBIOME_VARS = [
    "Bacteroides", "Firmicutes", "Actinobacteria", "Proteobacteria",
    "Faecalibacterium", "Akkermansia", "Roseburia", "Bifidobacterium"
]
REQUIRED_SLEEP_VARS = [
    "Total_Sleep_Time", "Sleep_Efficiency", "SWS_Duration", "REM_Duration",
    "Sleep_Onset_Latency", "Wake_After_Sleep_Onset"
]

# Mock metadata for known public datasets that might be candidates
# In a real scenario, this would be populated by T049 search results
KNOWN_DATASETS = [
    {
        "name": "Mock_GutSleep_Cohort_A",
        "source": "Synthetic/Placeholder for evaluation logic",
        "n_samples": 100,
        "has_microbiome": True,
        "has_sleep": True,
        "microbiome_type": "16S",
        "sleep_type": "Actigraphy",
        "privacy": "Open",
        "format": "CSV"
    },
    {
        "name": "Mock_GutSleep_Cohort_B",
        "source": "Synthetic/Placeholder for evaluation logic",
        "n_samples": 50,
        "has_microbiome": True,
        "has_sleep": False, # Missing sleep data
        "microbiome_type": "Shotgun",
        "sleep_type": "None",
        "privacy": "Restricted",
        "format": "CSV"
    },
    {
        "name": "Mock_GutSleep_Cohort_C",
        "source": "Synthetic/Placeholder for evaluation logic",
        "n_samples": 200,
        "has_microbiome": False, # Missing microbiome
        "has_sleep": True,
        "microbiome_type": "None",
        "sleep_type": "PSG",
        "privacy": "Open",
        "format": "CSV"
    }
]

def load_dataset_metadata(dataset_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Loads metadata for a list of candidate datasets.
    In a real implementation, this would fetch details from a registry or file.
    """
    return dataset_list

def evaluate_data_quality(dataset_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates data quality based on sample size and data type suitability.
    Returns a score (0-100) and specific notes.
    """
    score = 50
    notes = []

    n = dataset_info.get("n_samples", 0)
    if n >= 200:
        score += 30
        notes.append("Large sample size (>200)")
    elif n >= 100:
        score += 15
        notes.append("Moderate sample size (100-200)")
    else:
        notes.append("Small sample size (<100), may be underpowered")

    if dataset_info.get("microbiome_type") == "Shotgun":
        score += 10
        notes.append("High-resolution shotgun metagenomics")
    elif dataset_info.get("microbiome_type") == "16S":
        score += 5
        notes.append("16S rRNA sequencing (lower resolution)")

    if dataset_info.get("sleep_type") == "PSG":
        score += 10
        notes.append("Gold-standard Polysomnography")
    elif dataset_info.get("sleep_type") == "Actigraphy":
        score += 5
        notes.append("Actigraphy (good for long-term, lower resolution)")

    return {"score": score, "notes": notes}

def evaluate_variable_completeness(dataset_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates if the dataset contains required variables.
    Returns a boolean and a list of missing variables.
    """
    missing_microbiome = []
    missing_sleep = []

    # Simulate checking presence of variables based on metadata flags
    if not dataset_info.get("has_microbiome", False):
        missing_microbiome = REQUIRED_MICROBIOME_VARS
    else:
        # Simulate partial presence for the mock dataset
        missing_microbiome = [] 

    if not dataset_info.get("has_sleep", False):
        missing_sleep = REQUIRED_SLEEP_VARS
    else:
        missing_sleep = []

    total_missing = len(missing_microbiome) + len(missing_sleep)
    is_complete = total_missing == 0

    return {
        "is_complete": is_complete,
        "missing_microbiome_vars": missing_microbiome,
        "missing_sleep_vars": missing_sleep,
        "completeness_score": 100 if is_complete else max(0, 100 - (total_missing * 5))
    }

def evaluate_privacy_constraints(dataset_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates privacy constraints and accessibility.
    """
    privacy = dataset_info.get("privacy", "Unknown")
    score = 0
    notes = []

    if privacy == "Open":
        score = 100
        notes.append("Open access, no restrictions")
    elif privacy == "Restricted":
        score = 50
        notes.append("Restricted access, requires application/ethics approval")
    elif privacy == "Confidential":
        score = 0
        notes.append("Confidential, not publicly available")
    else:
        notes.append("Privacy status unknown")

    return {"score": score, "notes": notes, "access_level": privacy}

def evaluate_dataset(dataset_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs all evaluations for a single dataset and aggregates results.
    """
    quality = evaluate_data_quality(dataset_info)
    completeness = evaluate_variable_completeness(dataset_info)
    privacy = evaluate_privacy_constraints(dataset_info)

    # Weighted final score
    # Quality: 30%, Completeness: 50%, Privacy: 20%
    final_score = (
        (quality["score"] * 0.3) +
        (completeness["completeness_score"] * 0.5) +
        (privacy["score"] * 0.2)
    )

    return {
        "dataset_name": dataset_info["name"],
        "source": dataset_info["source"],
        "n_samples": dataset_info["n_samples"],
        "quality_score": quality["score"],
        "quality_notes": quality["notes"],
        "completeness_score": completeness["completeness_score"],
        "is_complete": completeness["is_complete"],
        "missing_vars": completeness["missing_microbiome_vars"] + completeness["missing_sleep_vars"],
        "privacy_score": privacy["score"],
        "access_level": privacy["access_level"],
        "final_weighted_score": final_score,
        "recommendation": "Suitable" if final_score > 60 and completeness["is_complete"] else "Needs Review"
    }

def generate_evaluation_matrix(datasets: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generates the CSV evaluation matrix as required by T050.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = [evaluate_dataset(ds) for ds in datasets]

    fieldnames = [
        "dataset_name", "source", "n_samples", "quality_score", "completeness_score",
        "is_complete", "missing_vars", "privacy_score", "access_level",
        "final_weighted_score", "recommendation"
    ]

    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            # Convert lists to strings for CSV
            row = res.copy()
            row['missing_vars'] = "; ".join(row['missing_vars']) if isinstance(row['missing_vars'], list) else ""
            row['quality_notes'] = "; ".join(row['quality_notes']) if isinstance(row['quality_notes'], list) else ""
            writer.writerow(row)

    print(f"Evaluation matrix generated at: {output_path}")

def main():
    """
    Main entry point to execute T050.
    """
    print("Starting Dataset Evaluation (Task T050)...")
    
    # In a real scenario, this list would come from T049 search results
    # For now, we use the known mock datasets to demonstrate the logic
    candidate_datasets = KNOWN_DATASETS

    if not candidate_datasets:
        print("No candidate datasets found. Skipping evaluation.")
        return

    generate_evaluation_matrix(candidate_datasets, EVALUATION_MATRIX_PATH)
    print("Task T050 completed successfully.")

if __name__ == "__main__":
    main()
