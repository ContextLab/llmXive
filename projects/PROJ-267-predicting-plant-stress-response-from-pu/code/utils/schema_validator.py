"""
Data schema validation module for plant stress response project.
Validates CSV/Parquet files in data/raw/ and data/processed/ directories.
"""
import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

# Import configuration from existing utility
from code.utils.config import PROJECT_ROOT, DATA_RAW_PATH, DATA_PROCESSED_PATH

@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    file_path: str = ""
    schema_name: str = ""

class SchemaValidator:
    """
    Validates data files against predefined schemas.
    Supports both Pydantic-style dict checks and simple column validation.
    """

    # Define schemas for different data types
    RAW_PROTEOMIC_SCHEMA = {
        "required_columns": {"Protein_ID", "Sample_ID", "Condition", "Abundance"},
        "optional_columns": {"Gene_Symbol", "Organism", "P_value", "Fold_Change"},
        "column_types": {
            "Protein_ID": str,
            "Sample_ID": str,
            "Condition": str,
            "Abundance": (int, float),
            "Gene_Symbol": str,
            "Organism": str,
            "P_value": (int, float),
            "Fold_Change": (int, float)
        },
        "valid_conditions": {"drought", "salinity", "heat", "control"}
    }

    PROCESSED_SCHEMA = {
        "required_columns": {"Protein_ID", "Sample_ID", "StressCondition", "Normalized_Abundance"},
        "optional_columns": {"Imputed", "Gene_Symbol", "Organism"},
        "column_types": {
            "Protein_ID": str,
            "Sample_ID": str,
            "StressCondition": str,
            "Normalized_Abundance": (int, float),
            "Imputed": bool,
            "Gene_Symbol": str,
            "Organism": str
        },
        "valid_conditions": {"drought", "salinity", "heat"}
    }

    METADATA_SCHEMA = {
        "required_columns": {"Sample_ID", "Organism", "StressCondition", "Replicate", "Source"},
        "optional_columns": {"Date", "Protocol", "Notes"},
        "column_types": {
            "Sample_ID": str,
            "Organism": str,
            "StressCondition": str,
            "Replicate": (int, float),
            "Source": str,
            "Date": str,
            "Protocol": str,
            "Notes": str
        },
        "valid_conditions": {"drought", "salinity", "heat", "control"}
    }

    def __init__(self):
        self.validation_results: List[ValidationResult] = []

    def _detect_schema_type(self, file_path: Path) -> Optional[str]:
        """Detect which schema to use based on file path and content."""
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        
        if "raw" in relative_path.lower():
            # Check if it looks like proteomic data
            return "RAW_PROTEOMIC_SCHEMA"
        elif "processed" in relative_path.lower():
            return "PROCESSED_SCHEMA"
        elif "metadata" in relative_path.lower():
            return "METADATA_SCHEMA"
        
        return None

    def _read_csv_header(self, file_path: Path) -> List[str]:
        """Read CSV header safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                return next(reader, [])
        except Exception as e:
            raise ValueError(f"Failed to read CSV header from {file_path}: {str(e)}")

    def _validate_columns(self, headers: List[str], schema: Dict, file_path: Path) -> ValidationResult:
        """Validate that required columns exist and types are correct."""
        result = ValidationResult(is_valid=True, file_path=str(file_path))
        headers_set = set(headers)
        
        # Check required columns
        required = schema.get("required_columns", set())
        missing = required - headers_set
        if missing:
            result.is_valid = False
            result.errors.append(f"Missing required columns: {missing}")
        
        # Check for unexpected columns (optional warning)
        optional = schema.get("optional_columns", set())
        all_known = required | optional
        unknown = headers_set - all_known
        if unknown:
            result.warnings.append(f"Unexpected columns found: {unknown}")
        
        return result

    def _validate_data_values(self, file_path: Path, schema: Dict) -> ValidationResult:
        """Validate data values against schema constraints."""
        result = ValidationResult(is_valid=True, file_path=str(file_path))
        schema_type = self._detect_schema_type(file_path)
        
        if not schema_type:
            return result

        schema_def = getattr(self, schema_type)
        valid_conditions = schema_def.get("valid_conditions", set())
        column_types = schema_def.get("column_types", {})
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                
                # Check condition column if it exists
                condition_col = None
                for col in ["Condition", "StressCondition"]:
                    if col in headers:
                        condition_col = col
                        break
                
                if condition_col and valid_conditions:
                    for i, row in enumerate(reader):
                        value = row.get(condition_col, "").lower().strip()
                        if value and value not in valid_conditions:
                            result.warnings.append(
                                f"Row {i+2}: Invalid condition '{value}'. "
                                f"Expected one of: {valid_conditions}"
                            )
                            
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Error reading data values: {str(e)}")
        
        return result

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single data file."""
        if not file_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"File does not exist: {file_path}"],
                file_path=str(file_path)
            )
        
        if file_path.suffix.lower() not in ['.csv', '.tsv']:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported file format: {file_path.suffix}"],
                file_path=str(file_path)
            )
        
        result = ValidationResult(
            is_valid=True,
            file_path=str(file_path),
            schema_name=self._detect_schema_type(file_path) or "unknown"
        )
        
        try:
            # Validate header
            headers = self._read_csv_header(file_path)
            if not headers:
                result.is_valid = False
                result.errors.append("File is empty or has no header")
                return result
            
            schema_type = self._detect_schema_type(file_path)
            if schema_type:
                schema_def = getattr(self, schema_type)
                col_result = self._validate_columns(headers, schema_def, file_path)
                result.errors.extend(col_result.errors)
                result.warnings.extend(col_result.warnings)
                result.is_valid = result.is_valid and col_result.is_valid
            
            # Validate data values
            if result.is_valid:
                val_result = self._validate_data_values(file_path, {})
                result.warnings.extend(val_result.warnings)
                result.is_valid = result.is_valid and val_result.is_valid
                
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Validation error: {str(e)}")
        
        return result

    def validate_directory(self, directory: Path, schema_type: Optional[str] = None) -> List[ValidationResult]:
        """Validate all CSV files in a directory."""
        results = []
        
        if not directory.exists():
            results.append(ValidationResult(
                is_valid=False,
                errors=[f"Directory does not exist: {directory}"],
                schema_name=schema_type or "unknown"
            ))
            return results
        
        csv_files = list(directory.glob("*.csv")) + list(directory.glob("*.tsv"))
        
        if not csv_files:
            results.append(ValidationResult(
                is_valid=True,
                warnings=["No CSV/TSV files found in directory"],
                schema_name=schema_type or "unknown"
            ))
            return results
        
        for file_path in csv_files:
            result = self.validate_file(file_path)
            results.append(result)
        
        return results

    def validate_all(self) -> Dict[str, Any]:
        """Validate both raw and processed data directories."""
        raw_results = self.validate_directory(DATA_RAW_PATH, "raw")
        processed_results = self.validate_directory(DATA_PROCESSED_PATH, "processed")
        
        all_valid = all(r.is_valid for r in raw_results + processed_results)
        
        return {
            "is_valid": all_valid,
            "raw_directory": {
                "path": str(DATA_RAW_PATH),
                "files_validated": len(raw_results),
                "errors": [r.errors for r in raw_results if r.errors],
                "warnings": [r.warnings for r in raw_results if r.warnings]
            },
            "processed_directory": {
                "path": str(DATA_PROCESSED_PATH),
                "files_validated": len(processed_results),
                "errors": [r.errors for r in processed_results if r.errors],
                "warnings": [r.warnings for r in processed_results if r.warnings]
            },
            "summary": {
                "total_files": len(raw_results) + len(processed_results),
                "valid_files": sum(1 for r in raw_results + processed_results if r.is_valid),
                "invalid_files": sum(1 for r in raw_results + processed_results if not r.is_valid)
            }
        }


def main():
    """Main entry point for schema validation."""
    print("Starting data schema validation...")
    
    validator = SchemaValidator()
    results = validator.validate_all()
    
    # Print summary
    print(f"\nValidation Summary:")
    print(f"  Total files: {results['summary']['total_files']}")
    print(f"  Valid files: {results['summary']['valid_files']}")
    print(f"  Invalid files: {results['summary']['invalid_files']}")
    print(f"  Overall status: {'PASS' if results['is_valid'] else 'FAIL'}")
    
    # Print errors if any
    if results['raw_directory']['errors']:
        print("\nRaw directory errors:")
        for error_list in results['raw_directory']['errors']:
            for error in error_list:
                print(f"  - {error}")
    
    if results['processed_directory']['errors']:
        print("\nProcessed directory errors:")
        for error_list in results['processed_directory']['errors']:
            for error in error_list:
                print(f"  - {error}")
    
    # Write detailed results to JSON
    output_path = PROJECT_ROOT / "results" / "schema_validation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results written to: {output_path}")
    
    if not results['is_valid']:
        print("\nValidation FAILED. Please fix the errors above.")
        return 1
    else:
        print("\nValidation PASSED.")
        return 0


if __name__ == "__main__":
    exit(main())
