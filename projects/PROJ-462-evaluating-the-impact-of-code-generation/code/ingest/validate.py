"""
Data ingestion validation module for US1.
Implements variable presence checks, missing data analysis, and dataset validation.
"""
import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.logging import get_validate_logger, log_validation_result

logger = get_validate_logger()

# Required variables as defined in spec
REQUIRED_VARIABLES = [
    "tool_usage",
    "task_time",
    "defect_rate",
    "experience_years",
    "task_complexity",
    "project_type",
    "team_size"
]

# Experience classification thresholds (from T008b)
EXPERIENCE_THRESHOLDS = {
    "novice": 2,
    "intermediate": 5
}


class ValidationResult:
    """Data structure to hold validation results."""
    
    def __init__(
        self,
        dataset_name: str,
        variables_found: List[str],
        variables_missing: List[str],
        missing_data_stats: Dict[str, Dict[str, Any]],
        is_valid: bool,
        timestamp: Optional[datetime] = None
    ):
        self.dataset_name = dataset_name
        self.variables_found = variables_found
        self.variables_missing = variables_missing
        self.missing_data_stats = missing_data_stats
        self.is_valid = is_valid
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dataset_name": self.dataset_name,
            "variables_found": self.variables_found,
            "variables_missing": self.variables_missing,
            "missing_data_stats": self.missing_data_stats,
            "is_valid": self.is_valid,
            "timestamp": self.timestamp.isoformat()
        }


def load_verified_datasets_from_spec() -> List[Dict[str, Any]]:
    """Load verified datasets from spec.md."""
    spec_path = Path("specs/001-code-generation-performance-outcomes/spec.md")
    
    if not spec_path.exists():
        logger.error(f"Spec file not found at {spec_path}")
        return []
    
    verified_datasets = []
    in_verified_block = False
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        if "# Verified datasets" in line:
            in_verified_block = True
            continue
        
        if in_verified_block:
            if line.strip().startswith("- [X] T000") or (line.strip() and not line.strip().startswith("-") and not line.strip().startswith("  ")):
                # End of verified datasets block
                in_verified_block = False
                continue
            
            if line.strip().startswith("- "):
                dataset_info = {}
                # Parse dataset entry
                parts = line.strip()[2:].split(" - ")
                if len(parts) >= 1:
                    dataset_info["name"] = parts[0].strip()
                if len(parts) >= 2:
                    dataset_info["url"] = parts[1].strip()
                if len(parts) >= 3:
                    dataset_info["checksum"] = parts[2].strip()
                verified_datasets.append(dataset_info)
    
    return verified_datasets


def load_csv_header(csv_path: str) -> List[str]:
    """Load and return the header row from a CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        
        if header is None:
            raise ValueError(f"CSV file is empty: {csv_path}")
        
        return [col.strip() for col in header]


def check_csv_variables(csv_path: str, required_vars: List[str]) -> Tuple[List[str], List[str]]:
    """Check which required variables are present in the CSV header."""
    try:
        header = load_csv_header(csv_path)
        found = []
        missing = []
        
        for var in required_vars:
            if var in header:
                found.append(var)
            else:
                missing.append(var)
        
        return found, missing
    except Exception as e:
        logger.error(f"Error checking CSV variables: {e}")
        raise


def check_tool_usage_variable(csv_path: str) -> bool:
    """Check if the tool_usage variable is present in the dataset."""
    try:
        header = load_csv_header(csv_path)
        return "tool_usage" in header
    except Exception as e:
        logger.error(f"Error checking tool_usage variable: {e}")
        return False


def check_task_time_variable(csv_path: str) -> bool:
    """Check if the task_time variable is present in the dataset."""
    try:
        header = load_csv_header(csv_path)
        return "task_time" in header
    except Exception as e:
        logger.error(f"Error checking task_time variable: {e}")
        return False


def check_defect_rate_variable(csv_path: str) -> bool:
    """Check if the defect_rate variable is present in the dataset."""
    try:
        header = load_csv_header(csv_path)
        return "defect_rate" in header
    except Exception as e:
        logger.error(f"Error checking defect_rate variable: {e}")
        return False


def check_experience_years_variable(csv_path: str) -> bool:
    """Check if the experience_years variable is present in the dataset."""
    try:
        header = load_csv_header(csv_path)
        return "experience_years" in header
    except Exception as e:
        logger.error(f"Error checking experience_years variable: {e}")
        return False


def identify_missing_experience_values(csv_path: str, threshold: float = 0.0) -> List[int]:
    """
    Identify row indices where experience_years data is missing.
    
    Args:
        csv_path: Path to the CSV file
        threshold: Minimum value to consider as valid (default 0)
    
    Returns:
        List of row indices with missing or invalid experience data
    """
    missing_indices = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check if experience_years column exists
            if "experience_years" not in reader.fieldnames:
                logger.error("experience_years column not found in CSV")
                return list(range(100))  # Return placeholder indices if column missing
            
            for row_idx, row in enumerate(reader, start=1):
                exp_value = row.get("experience_years", "").strip()
                
                # Check for missing values
                if not exp_value:
                    missing_indices.append(row_idx)
                else:
                    try:
                        exp_float = float(exp_value)
                        if exp_float < threshold:
                            missing_indices.append(row_idx)
                    except ValueError:
                        missing_indices.append(row_idx)
    
    except Exception as e:
        logger.error(f"Error identifying missing experience values: {e}")
        raise
    
    return missing_indices


def calculate_missing_percentage(csv_path: str, column_name: str) -> float:
    """
    Calculate the percentage of missing entries for a specific column.
    
    Args:
        csv_path: Path to the CSV file
        column_name: Name of the column to check for missing values
    
    Returns:
        Percentage of missing entries (0.0 to 100.0)
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    total_rows = 0
    missing_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check if column exists
            if column_name not in reader.fieldnames:
                logger.warning(f"Column '{column_name}' not found in CSV. Returning 100% missing.")
                return 100.0
            
            for row in reader:
                total_rows += 1
                value = row.get(column_name, "").strip()
                
                # Check for missing values
                if not value:
                    missing_count += 1
                else:
                    # Also check for invalid numeric values if column should be numeric
                    if column_name in ["experience_years", "task_time", "defect_rate", "task_complexity", "team_size"]:
                        try:
                            float(value)
                        except ValueError:
                            missing_count += 1
    
    except Exception as e:
        logger.error(f"Error calculating missing percentage: {e}")
        raise
    
    if total_rows == 0:
        return 0.0
    
    percentage = (missing_count / total_rows) * 100.0
    logger.info(f"Missing percentage for {column_name}: {percentage:.2f}% ({missing_count}/{total_rows} rows)")
    
    return percentage


def filter_missing_data(csv_path: str, output_path: str, columns_to_check: List[str], max_missing_pct: float = 20.0) -> bool:
    """
    Filter out rows with missing data in specified columns.
    
    Args:
        csv_path: Input CSV path
        output_path: Output CSV path
        columns_to_check: List of columns to check for missing values
        max_missing_pct: Maximum allowed percentage of missing data (default 20%)
    
    Returns:
        True if filtering succeeded, False if data exceeds missing threshold
    """
    try:
        # Calculate missing percentage for each column
        missing_stats = {}
        for col in columns_to_check:
            pct = calculate_missing_percentage(csv_path, col)
            missing_stats[col] = pct
            
            if pct > max_missing_pct:
                logger.warning(f"Column '{col}' has {pct:.2f}% missing data, exceeds threshold of {max_missing_pct}%")
        
        # Check if any column exceeds threshold
        if any(pct > max_missing_pct for pct in missing_stats.values()):
            logger.error(f"Data exceeds missing threshold. Cannot proceed with filtering.")
            return False
        
        # Filter rows
        with open(csv_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            
            filtered_count = 0
            original_count = 0
            
            for row in reader:
                original_count += 1
                has_missing = False
                
                for col in columns_to_check:
                    if not row.get(col, "").strip():
                        has_missing = True
                        break
                
                if not has_missing:
                    writer.writerow(row)
                else:
                    filtered_count += 1
            
            logger.info(f"Filtered {filtered_count} rows out of {original_count} total rows")
            return True
    
    except Exception as e:
        logger.error(f"Error filtering missing data: {e}")
        return False


def validate_dataset_from_url(url: str, expected_checksum: str) -> ValidationResult:
    """
    Validate a dataset downloaded from a URL.
    
    Args:
        url: Dataset URL
        expected_checksum: Expected SHA-256 checksum
    
    Returns:
        ValidationResult object
    """
    from ingest.download import download_dataset, verify_checksum
    
    dataset_name = url.split("/")[-1].split("?")[0]
    temp_path = f"data/raw/{dataset_name}"
    
    try:
        # Download dataset
        download_dataset(url, temp_path)
        
        # Verify checksum
        if not verify_checksum(temp_path, expected_checksum):
            logger.error(f"Checksum verification failed for {dataset_name}")
            return ValidationResult(
                dataset_name=dataset_name,
                variables_found=[],
                variables_missing=REQUIRED_VARIABLES,
                missing_data_stats={},
                is_valid=False
            )
        
        # Check variables
        found, missing = check_csv_variables(temp_path, REQUIRED_VARIABLES)
        
        # Calculate missing data stats for key columns
        missing_stats = {}
        key_columns = ["tool_usage", "task_time", "defect_rate", "experience_years"]
        
        for col in key_columns:
            if col in found:
                pct = calculate_missing_percentage(temp_path, col)
                missing_stats[col] = {
                    "missing_percentage": pct,
                    "is_critical": pct > 20.0
                }
        
        is_valid = len(missing) == 0 and all(stats["missing_percentage"] <= 20.0 for stats in missing_stats.values())
        
        return ValidationResult(
            dataset_name=dataset_name,
            variables_found=found,
            variables_missing=missing,
            missing_data_stats=missing_stats,
            is_valid=is_valid
        )
    
    except Exception as e:
        logger.error(f"Error validating dataset from URL: {e}")
        return ValidationResult(
            dataset_name=dataset_name,
            variables_found=[],
            variables_missing=REQUIRED_VARIABLES,
            missing_data_stats={},
            is_valid=False
        )


def validate_all_datasets() -> List[ValidationResult]:
    """Validate all verified datasets from spec.md."""
    datasets = load_verified_datasets_from_spec()
    results = []
    
    for dataset in datasets:
        logger.info(f"Validating dataset: {dataset.get('name', 'Unknown')}")
        result = validate_dataset_from_url(
            dataset.get("url", ""),
            dataset.get("checksum", "")
        )
        results.append(result)
        log_validation_result(result)
    
    return results


def generate_validation_report(results: List[ValidationResult], output_path: str):
    """Generate a JSON validation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_datasets": len(results),
        "valid_datasets": sum(1 for r in results if r.is_valid),
        "results": [r.to_dict() for r in results]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")


def main():
    """Main function for running validation."""
    logger.info("Starting dataset validation...")
    
    # Validate all verified datasets
    results = validate_all_datasets()
    
    # Generate report
    report_path = "data/output/validation_report.json"
    generate_validation_report(results, report_path)
    
    # Print summary
    valid_count = sum(1 for r in results if r.is_valid)
    print(f"Validation complete: {valid_count}/{len(results)} datasets valid")
    
    return results


if __name__ == "__main__":
    main()