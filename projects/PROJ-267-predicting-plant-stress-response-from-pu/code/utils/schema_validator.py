"""
Data schema validation module for raw and processed data directories.

Implements validation logic using Pydantic models where possible,
and fallback dict checks for complex or dynamic schemas.
"""
import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

# Try to import pydantic, fallback to dict-based validation if not available
try:
    from pydantic import BaseModel, Field, ValidationError, field_validator
    from pydantic.config import ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Define a simple fallback structure if Pydantic is not available
    class BaseModel:
        pass
    class Field:
        def __init__(self, default=None, **kwargs):
            self.default = default
    class ValidationError(Exception):
        pass

from .config import DATA_RAW_PATH, DATA_PROCESSED_PATH, LOG_PATH
from .logging_config import get_logger, log_warning

logger = get_logger(__name__)

class ValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class ValidationResult:
    file_path: str
    status: ValidationStatus
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_name: str = "unknown"

class SchemaValidator:
    """
    Validates data files against predefined schemas.
    Supports both Pydantic models and dict-based checks.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_RAW_PATH
        self.logger = get_logger(__name__)
        
        # Define schemas for common data types
        self.schemas = {
            "raw_proteomics": self._validate_raw_proteomics,
            "raw_transcriptomics": self._validate_raw_transcriptomics,
            "processed_matrix": self._validate_processed_matrix,
            "metadata": self._validate_metadata,
        }

    def _validate_raw_proteomics(self, file_path: Path, content: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate raw proteomics data.
        Expected columns: ProteinID, SampleID, Abundance, StressCondition, Species
        """
        errors = []
        warnings = []
        
        required_columns = {"ProteinID", "SampleID", "Abundance", "StressCondition", "Species"}
        if not content:
            errors.append("File is empty or contains no data rows")
            return ValidationResult(str(file_path), ValidationStatus.INVALID, errors, warnings, "raw_proteomics")
        
        headers = set(content[0].keys())
        missing_cols = required_columns - headers
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Validate data types and constraints
        for i, row in enumerate(content[:100]):  # Sample check for performance
            if not row.get("ProteinID"):
                warnings.append(f"Row {i}: Missing ProteinID")
            if row.get("Abundance") is not None:
                try:
                    float(row["Abundance"])
                except (ValueError, TypeError):
                    errors.append(f"Row {i}: Abundance is not a valid number")
        
        status = ValidationStatus.INVALID if errors else ValidationStatus.VALID
        return ValidationResult(str(file_path), status, errors, warnings, "raw_proteomics")

    def _validate_raw_transcriptomics(self, file_path: Path, content: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate raw transcriptomics data.
        Expected columns: GeneID, SampleID, Expression, StressCondition, Species
        """
        errors = []
        warnings = []
        
        required_columns = {"GeneID", "SampleID", "Expression", "StressCondition", "Species"}
        if not content:
            errors.append("File is empty or contains no data rows")
            return ValidationResult(str(file_path), ValidationStatus.INVALID, errors, warnings, "raw_transcriptomics")
        
        headers = set(content[0].keys())
        missing_cols = required_columns - headers
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        status = ValidationStatus.INVALID if errors else ValidationStatus.VALID
        return ValidationResult(str(file_path), status, errors, warnings, "raw_transcriptomics")

    def _validate_processed_matrix(self, file_path: Path, content: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate processed data matrix.
        Expected columns: ID (Protein or Gene), Sample1, Sample2, ..., StressCondition, Species
        """
        errors = []
        warnings = []
        
        if not content:
            errors.append("File is empty or contains no data rows")
            return ValidationResult(str(file_path), ValidationStatus.INVALID, errors, warnings, "processed_matrix")
        
        headers = set(content[0].keys())
        # At minimum, expect an ID column and at least one sample column
        id_cols = [h for h in headers if h.lower() in ["id", "proteinid", "geneid"]]
        if not id_cols:
            errors.append("Missing ID column (expected 'ID', 'ProteinID', or 'GeneID')")
        
        sample_cols = [h for h in headers if h not in ["ID", "ProteinID", "GeneID", "StressCondition", "Species"]]
        if not sample_cols:
            warnings.append("No sample columns found. Check if data was properly processed.")
        
        status = ValidationStatus.INVALID if errors else ValidationStatus.VALID
        return ValidationResult(str(file_path), status, errors, warnings, "processed_matrix")

    def _validate_metadata(self, file_path: Path, content: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate metadata JSON/CSV files.
        Expected structure varies, but must contain 'source', 'date', 'description'
        """
        errors = []
        warnings = []
        
        if not content:
            errors.append("Metadata file is empty")
            return ValidationResult(str(file_path), ValidationStatus.INVALID, errors, warnings, "metadata")
        
        required_fields = {"source", "date", "description"}
        first_row = content[0]
        missing_fields = required_fields - set(first_row.keys())
        if missing_fields:
            errors.append(f"Missing required metadata fields: {missing_fields}")
        
        status = ValidationStatus.INVALID if errors else ValidationStatus.VALID
        return ValidationResult(str(file_path), status, errors, warnings, "metadata")

    def _detect_schema_type(self, file_path: Path) -> str:
        """
        Detect which schema to apply based on file name and content.
        """
        file_name = file_path.name.lower()
        
        if "proteo" in file_name:
            return "raw_proteomics"
        elif "transcrip" in file_name or "rna" in file_name:
            return "raw_transcriptomics"
        elif "processed" in file_name or "matrix" in file_name:
            return "processed_matrix"
        elif "meta" in file_name:
            return "metadata"
        
        # Default to checking content for clues
        if file_path.suffix == '.csv':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    first_row = next(reader, None)
                    if first_row:
                        if "ProteinID" in first_row:
                            return "raw_proteomics"
                        elif "GeneID" in first_row:
                            return "raw_transcriptomics"
            except Exception as e:
                self.logger.warning(f"Could not detect schema for {file_path}: {e}")
        
        return "processed_matrix"  # Default fallback

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a single file against its detected schema.
        """
        if not file_path.exists():
            return ValidationResult(str(file_path), ValidationStatus.ERROR, [f"File not found: {file_path}"], [], "unknown")
        
        schema_type = self._detect_schema_type(file_path)
        validator_func = self.schemas.get(schema_type)
        
        if not validator_func:
            return ValidationResult(str(file_path), ValidationStatus.SKIPPED, [], [f"No validator for schema type: {schema_type}"], schema_type)
        
        content = []
        try:
            if file_path.suffix == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    content = list(reader)
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        content = data
                    elif isinstance(data, dict):
                        content = [data]
                    else:
                        return ValidationResult(str(file_path), ValidationStatus.ERROR, ["JSON must be a list or object"], [], schema_type)
            else:
                return ValidationResult(str(file_path), ValidationStatus.SKIPPED, [], [f"Unsupported file format: {file_path.suffix}"], schema_type)
        except Exception as e:
            return ValidationResult(str(file_path), ValidationStatus.ERROR, [f"Error reading file: {str(e)}"], [], schema_type)
        
        return validator_func(file_path, content)

    def validate_directory(self, directory: Optional[Path] = None) -> List[ValidationResult]:
        """
        Validate all files in a directory.
        """
        target_dir = directory or self.data_dir
        results = []
        
        if not target_dir.exists():
            self.logger.error(f"Directory does not exist: {target_dir}")
            return results
        
        supported_extensions = {'.csv', '.json', '.tsv'}
        
        for file_path in target_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                result = self.validate_file(file_path)
                results.append(result)
                if result.status == ValidationStatus.INVALID:
                    self.logger.error(f"Validation failed for {file_path}: {result.errors}")
                elif result.status == ValidationStatus.VALID:
                    self.logger.info(f"Validation passed for {file_path}")
                elif result.status == ValidationStatus.ERROR:
                    self.logger.error(f"Error validating {file_path}: {result.errors}")
        
        return results

def main():
    """
    Entry point for schema validation script.
    Validates both raw and processed data directories.
    """
    logger.info("Starting schema validation for data directories...")
    
    raw_validator = SchemaValidator(DATA_RAW_PATH)
    processed_validator = SchemaValidator(DATA_PROCESSED_PATH)
    
    raw_results = raw_validator.validate_directory(DATA_RAW_PATH)
    processed_results = processed_validator.validate_directory(DATA_PROCESSED_PATH)
    
    all_results = raw_results + processed_results
    
    valid_count = sum(1 for r in all_results if r.status == ValidationStatus.VALID)
    invalid_count = sum(1 for r in all_results if r.status == ValidationStatus.INVALID)
    error_count = sum(1 for r in all_results if r.status == ValidationStatus.ERROR)
    skipped_count = sum(1 for r in all_results if r.status == ValidationStatus.SKIPPED)
    
    logger.info(f"Validation Summary:")
    logger.info(f"  Valid: {valid_count}")
    logger.info(f"  Invalid: {invalid_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Skipped: {skipped_count}")
    
    if invalid_count > 0 or error_count > 0:
        logger.warning("Some files failed validation. Check logs for details.")
        return 1
    else:
        logger.info("All files passed validation.")
        return 0

if __name__ == "__main__":
    exit(main())