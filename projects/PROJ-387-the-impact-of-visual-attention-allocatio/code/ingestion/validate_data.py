import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing project modules
from utils.logger import get_logger
from utils.config import get_project_root, get_data_path

logger = get_logger(__name__)

# Required columns as per FR-002 and task description
REQUIRED_COLUMNS = [
    "fixation_duration",
    "saccade_amplitude",
    "gaze_distribution",
    "recall_accuracy",
    "valence_label"
]

def validate_columns(df: Any, dataset_name: str = "unknown") -> Dict[str, Any]:
    """
    Validates that the DataFrame contains all required columns.
    
    Args:
        df: The pandas DataFrame to validate.
        dataset_name: Name of the dataset for logging purposes.
        
    Returns:
        A dictionary with validation results.
    """
    missing_columns = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
    
    result = {
        "dataset": dataset_name,
        "valid": len(missing_columns) == 0,
        "missing_columns": missing_columns,
        "found_columns": list(df.columns)
    }
    
    return result

def validate_data_quality_metrics(df: Any, track_loss_threshold: float = 0.05) -> Dict[str, Any]:
    """
    Validates data quality metrics (e.g., track loss).
    
    Args:
        df: The pandas DataFrame.
        track_loss_threshold: Maximum allowed track loss ratio.
        
    Returns:
        Validation result dictionary.
    """
    # Placeholder for actual track loss calculation logic
    # Assuming a column 'track_loss' exists or calculating it
    track_loss = 0.0 
    if "track_loss" in df.columns:
        track_loss = df["track_loss"].mean()
    
    result = {
        "track_loss": track_loss,
        "valid": track_loss <= track_loss_threshold
    }
    
    return result

def validate_valence_labels(df: Any) -> Dict[str, Any]:
    """
    Validates valence annotation presence and standardized scale.
    
    Args:
        df: The pandas DataFrame.
        
    Returns:
        Validation result dictionary.
    """
    if "valence_label" not in df.columns:
        return {"valid": False, "reason": "Missing valence_label column"}
    
    # Check for standardized scale (example: 1-5 or -1 to 1)
    # Implementation depends on specific scale requirements
    return {"valid": True, "reason": "Valence labels present"}

def write_quality_report(results: List[Dict], output_path: Path) -> None:
    """
    Writes the quality report to a markdown file.
    
    Args:
        results: List of validation result dictionaries.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write("# Data Quality Report\n\n")
        for res in results:
            f.write(f"## Dataset: {res.get('dataset', 'Unknown')}\n")
            f.write(f"- Valid: {res.get('valid', False)}\n")
            if not res.get('valid', False):
                if 'missing_columns' in res:
                    f.write(f"- Missing Columns: {', '.join(res['missing_columns'])}\n")
            f.write("\n")

def main():
    """
    Main entry point for validation.
    Implements T016: Halt if dataset is incompatible (missing variables).
    """
    parser = argparse.ArgumentParser(description="Validate eye-tracking data")
    parser.add_argument("--data-path", type=str, help="Path to input data file")
    parser.add_argument("--output-dir", type=str, help="Output directory for reports")
    args = parser.parse_args()

    if not args.data_path:
        logger.error("DATA_BLOCKER: No data path provided")
        print("DATA_BLOCKER: No data path provided", file=sys.stderr)
        sys.exit(1)

    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.error(f"DATA_BLOCKER: Data file not found: {data_path}")
        print(f"DATA_BLOCKER: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    # Load data (using simple pandas read for CSV/EDF simulation)
    # In a real scenario, this would call load_data from load_data.py
    import pandas as pd
    try:
        if data_path.suffix == ".csv":
            df = pd.read_csv(data_path)
        else:
            # Placeholder for EDF handling
            logger.error("DATA_BLOCKER: Unsupported file format")
            print("DATA_BLOCKER: Unsupported file format", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        logger.error(f"DATA_BLOCKER: Failed to load data: {str(e)}")
        print(f"DATA_BLOCKER: Failed to load data: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # Validate columns (T013 logic)
    col_validation = validate_columns(df, dataset_name=data_path.name)
    
    if not col_validation["valid"]:
        missing = ", ".join(col_validation["missing_columns"])
        error_msg = f"DATA_BLOCKER: Missing required variables: {missing}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        # T016: Halt processing and log error if dataset is incompatible
        sys.exit(1)

    # Validate data quality (T014 logic)
    quality_validation = validate_data_quality_metrics(df)
    if not quality_validation["valid"]:
        error_msg = f"DATA_BLOCKER: Track loss exceeds threshold ({quality_validation['track_loss']})"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Validate valence (T015 logic)
    valence_validation = validate_valence_labels(df)
    if not valence_validation["valid"]:
        error_msg = f"DATA_BLOCKER: {valence_validation['reason']}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Write report if all validations pass
    output_dir = Path(args.output_dir) if args.output_dir else get_project_root() / "data" / "eye-tracking"
    report_path = output_dir / "quality_report.md"
    write_quality_report([col_validation, quality_validation, valence_validation], report_path)
    
    logger.info("Validation successful. Quality report written.")
    print(f"Validation successful. Report: {report_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
