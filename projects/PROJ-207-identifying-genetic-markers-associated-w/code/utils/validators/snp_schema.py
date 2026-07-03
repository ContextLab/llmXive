"""
Schema validator for SNP entities.
Validates against specs/001-gene-regulation/contracts/gwas_output.schema.yaml
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import re


@dataclass
class SnpSchema:
    """
    Defines the expected schema for a SNP record (GWAS output).
    Corresponds to the 'gwas_output.schema.yaml' definition for SNP entities.
    """
    # Required fields
    rs_id: str
    chromosome: str
    position: int
    allele1: str
    allele2: str
    p_value: float
    odds_ratio: Optional[float] = None
    beta: Optional[float] = None
    standard_error: Optional[float] = None
    effect_allele: Optional[str] = None
    non_effect_allele: Optional[str] = None
    q_value: Optional[float] = None  # FDR corrected p-value

    # Metadata for validation
    required_fields: List[str] = field(default_factory=lambda: [
        "rs_id", "chromosome", "position", "allele1", "allele2", "p_value"
    ])
    valid_alleles: List[str] = field(default_factory=lambda: ["A", "C", "G", "T", "-", "N"])


def validate_snp_data(data: Dict[str, Any]) -> List[str]:
    """
    Validates a single SNP record against the SnpSchema.

    Args:
        data: A dictionary representing a single SNP record.

    Returns:
        A list of error messages. Empty if validation passes.
    """
    errors = []
    schema = SnpSchema()

    # Check required fields
    for field_name in schema.required_fields:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")
        elif data[field_name] is None or data[field_name] == "":
            errors.append(f"Field '{field_name}' cannot be empty.")

    # Validate types and constraints for required fields
    if "rs_id" in data:
        if not isinstance(data["rs_id"], str):
            errors.append("rs_id must be a string.")
        # Check for common rsID format (rs followed by digits)
        elif not re.match(r'^rs\d+$', data["rs_id"], re.IGNORECASE):
            # Allow flexibility for custom IDs if they don't match rs format but are non-empty
            pass

    if "chromosome" in data:
        if not isinstance(data["chromosome"], (str, int)):
            errors.append("chromosome must be a string or integer.")
        elif str(data["chromosome"]) not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "X", "Y", "MT", "M"]:
            # Basic honeybee chromosome validation (haplodiploid, 16 chromosomes typically, but using standard format)
            # Honeybee (Apis mellifera) has 16 chromosomes.
            valid_chroms = [str(i) for i in range(1, 17)] + ["X", "Y", "MT", "M"]
            if str(data["chromosome"]).upper() not in valid_chroms:
                errors.append(f"Invalid chromosome: '{data['chromosome']}'. Must be 1-16 or X, Y, MT, M.")

    if "position" in data:
        if not isinstance(data["position"], int):
            errors.append("position must be an integer.")
        elif data["position"] <= 0:
            errors.append("position must be a positive integer.")

    if "allele1" in data:
        if not isinstance(data["allele1"], str) or len(data["allele1"]) != 1:
            errors.append("allele1 must be a single character string.")
        elif data["allele1"].upper() not in schema.valid_alleles:
            errors.append(f"Invalid allele1: '{data['allele1']}'. Must be one of: {schema.valid_alleles}")

    if "allele2" in data:
        if not isinstance(data["allele2"], str) or len(data["allele2"]) != 1:
            errors.append("allele2 must be a single character string.")
        elif data["allele2"].upper() not in schema.valid_alleles:
            errors.append(f"Invalid allele2: '{data['allele2']}'. Must be one of: {schema.valid_alleles}")

    if "p_value" in data:
        if not isinstance(data["p_value"], (int, float)):
            errors.append("p_value must be a number.")
        elif data["p_value"] < 0 or data["p_value"] > 1:
            errors.append("p_value must be between 0 and 1.")

    # Validate optional fields if present
    if "odds_ratio" in data and data["odds_ratio"] is not None:
        if not isinstance(data["odds_ratio"], (int, float)):
            errors.append("odds_ratio must be a number.")
        elif data["odds_ratio"] <= 0:
            errors.append("odds_ratio must be positive.")

    if "beta" in data and data["beta"] is not None:
        if not isinstance(data["beta"], (int, float)):
            errors.append("beta must be a number.")

    if "standard_error" in data and data["standard_error"] is not None:
        if not isinstance(data["standard_error"], (int, float)):
            errors.append("standard_error must be a number.")
        elif data["standard_error"] < 0:
            errors.append("standard_error cannot be negative.")

    if "q_value" in data and data["q_value"] is not None:
        if not isinstance(data["q_value"], (int, float)):
            errors.append("q_value must be a number.")
        elif data["q_value"] < 0 or data["q_value"] > 1:
            errors.append("q_value must be between 0 and 1.")

    return errors


def validate_snp_batch(data_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates a batch of SNP records.

    Args:
        data_batch: A list of dictionaries, each representing a SNP record.

    Returns:
        A dictionary with 'valid_count', 'invalid_count', and 'errors' list.
    """
    errors = []
    valid_count = 0
    invalid_count = 0

    for i, record in enumerate(data_batch):
        record_errors = validate_snp_data(record)
        if record_errors:
            invalid_count += 1
            for err in record_errors:
                errors.append(f"Record {i}: {err}")
        else:
            valid_count += 1

    return {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "errors": errors
    }