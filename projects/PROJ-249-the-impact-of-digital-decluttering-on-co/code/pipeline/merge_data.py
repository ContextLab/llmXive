import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define expected paths based on project structure
DATA_PROCESSED_DIR = Path("data/processed")
BASELINE_RAW_PATH = Path("data/raw/baseline_raw.csv")
COMPLIANCE_SCORES_PATH = Path("data/processed/compliance_scores.csv")
MERGED_OUTPUT_PATH = Path("data/processed/merged_data.csv")
EXCLUSIONS_PATH = Path("data/processed/exclusions.json")

def load_csv_data(file_path: Path, required_columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Load data from a CSV file into a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        required_columns: Optional list of columns that must be present
        
    Returns:
        List of dictionaries representing rows
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If required columns are missing
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        logger.warning(f"Loaded 0 rows from {file_path}")
        return data

    if required_columns:
        first_row_keys = set(data[0].keys())
        missing = set(required_columns) - first_row_keys
        if missing:
            raise ValueError(f"Missing required columns in {file_path}: {missing}")
    
    return data

def validate_compliance_scores(file_path: Path) -> bool:
    """
    Validate that the compliance scores file exists and has valid structure.
    This is a dependency check for T029 output.
    
    Args:
        file_path: Path to the compliance scores CSV
        
    Returns:
        True if valid
        
    Raises:
        FileNotFoundError: If file is missing
        ValueError: If structure is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dependency check failed: Compliance scores file not found at {file_path}. "
            "Please ensure T029 (aggregate_compliance) has run successfully."
        )
    
    try:
        data = load_csv_data(file_path)
        if not data:
            raise ValueError(f"Compliance scores file is empty: {file_path}")
        
        # Validate expected columns for compliance scores
        # Based on T029 output schema: participant_id, daily_score, weekly_score, compliance_rate
        expected_cols = {'participant_id', 'daily_score', 'weekly_score', 'compliance_rate'}
        actual_cols = set(data[0].keys())
        
        if not expected_cols.issubset(actual_cols):
            missing = expected_cols - actual_cols
            raise ValueError(f"Compliance scores file missing columns: {missing}")
        
        logger.info(f"Compliance scores validation passed: {len(data)} records found.")
        return True
        
    except Exception as e:
        logger.error(f"Compliance scores validation failed: {e}")
        raise

def merge_baseline_post(baseline_data: List[Dict], post_data: List[Dict]) -> List[Dict]:
    """
    Merge baseline and post-intervention data by participant_id.
    
    Args:
        baseline_data: List of baseline records
        post_data: List of post-intervention records
        
    Returns:
        Merged list of records
    """
    # Index post data by participant_id
    post_map = {row['participant_id']: row for row in post_data}
    
    merged = []
    for row in baseline_data:
        pid = row['participant_id']
        new_row = dict(row)
        if pid in post_map:
            # Add post-intervention columns with prefix or direct mapping
            # Assuming schema: baseline has 'metric_type', 'value'; post has same
            # We need to handle the join logic carefully
            post_row = post_map[pid]
            for key, val in post_row.items():
                if key != 'participant_id':
                    new_row[f'post_{key}'] = val
        merged.append(new_row)
    
    return merged

def merge_compliance(merged_data: List[Dict], compliance_data: List[Dict]) -> List[Dict]:
    """
    Merge compliance scores into the merged dataset.
    This function enforces the dependency on T029.
    
    Args:
        merged_data: List of merged baseline/post records
        compliance_data: List of compliance score records
        
    Returns:
        Updated merged list with compliance data
    """
    # Index compliance data by participant_id
    compliance_map = {row['participant_id']: row for row in compliance_data}
    
    result = []
    for row in merged_data:
        pid = row['participant_id']
        new_row = dict(row)
        if pid in compliance_map:
            comp_row = compliance_map[pid]
            for key, val in comp_row.items():
                if key != 'participant_id':
                    new_row[f'comp_{key}'] = val
        else:
            # Log warning but do not fail; some participants might not have compliance data
            logger.warning(f"No compliance data found for participant {pid}")
        result.append(new_row)
    
    return result

def write_merged_data(data: List[Dict], output_path: Path) -> None:
    """
    Write merged data to a CSV file.
    
    Args:
        data: List of dictionaries to write
        output_path: Path to output file
    """
    if not data:
        logger.warning("No data to write to merged file.")
        # Create empty file with headers if needed, or skip
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("")
        return

    fieldnames = list(data[0].keys())
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Wrote {len(data)} records to {output_path}")

def run_merge_pipeline(baseline_path: Path = BASELINE_RAW_PATH, 
                       compliance_path: Path = COMPLIANCE_SCORES_PATH,
                       output_path: Path = MERGED_OUTPUT_PATH) -> Dict[str, Any]:
    """
    Run the full merge pipeline with dependency checks.
    
    This function implements T054:
    - Verifies that compliance_scores.csv (from T029) exists before merging.
    - Merges baseline and post data.
    - Merges compliance scores.
    - Writes the final merged dataset.
    
    Args:
        baseline_path: Path to baseline raw data
        compliance_path: Path to compliance scores (T029 output)
        output_path: Path for merged output
        
    Returns:
        Dictionary with pipeline status and counts
        
    Raises:
        FileNotFoundError: If mandatory dependencies are missing
    """
    logger.info("Starting merge data pipeline...")
    
    # 1. Dependency Check (T054 Requirement)
    logger.info(f"Checking dependency: {compliance_path}")
    try:
        validate_compliance_scores(compliance_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Pipeline aborted due to missing/invalid dependency: {e}")
        raise

    # 2. Load Baseline Data
    logger.info(f"Loading baseline data from {baseline_path}")
    try:
        baseline_data = load_csv_data(baseline_path)
    except FileNotFoundError:
        # Handle case where baseline might be missing (though less likely to be a dependency error)
        logger.error(f"Baseline data not found: {baseline_path}")
        raise

    # 3. Load Post-Intervention Data
    # Assuming post data is in a separate file or part of baseline_raw with a flag
    # For this implementation, we assume a standard structure where post data might be
    # in data/raw/post_intervention_raw.csv or similar. 
    # However, looking at T031 context, it merges baseline and post.
    # Let's assume post data is in data/raw/post_intervention_raw.csv for now, 
    # or if not available, we treat baseline as the only source and merge compliance.
    # Based on T032 (change scores), we need paired data.
    # Let's assume there is a file 'data/raw/post_intervention_raw.csv'
    post_path = Path("data/raw/post_intervention_raw.csv")
    post_data = []
    if post_path.exists():
        logger.info(f"Loading post-intervention data from {post_path}")
        post_data = load_csv_data(post_path)
    else:
        logger.warning(f"Post-intervention data not found at {post_path}. Proceeding with baseline only.")

    # 4. Merge Baseline and Post
    merged_data = merge_baseline_post(baseline_data, post_data)
    logger.info(f"Baseline-Post merge complete: {len(merged_data)} records.")

    # 5. Load and Merge Compliance Data
    logger.info(f"Loading compliance data from {compliance_path}")
    compliance_data = load_csv_data(compliance_path)
    final_data = merge_compliance(merged_data, compliance_data)
    logger.info(f"Compliance merge complete: {len(final_data)} records.")

    # 6. Write Output
    logger.info(f"Writing merged data to {output_path}")
    write_merged_data(final_data, output_path)

    return {
        "status": "success",
        "baseline_count": len(baseline_data),
        "post_count": len(post_data),
        "compliance_count": len(compliance_data),
        "final_count": len(final_data),
        "output_path": str(output_path)
    }

def main():
    """Main entry point for the merge data script."""
    try:
        result = run_merge_pipeline()
        print(json.dumps(result, indent=2))
        logger.info("Merge pipeline completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()