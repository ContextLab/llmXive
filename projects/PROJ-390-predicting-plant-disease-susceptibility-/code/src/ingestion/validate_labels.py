"""
Validate disease susceptibility labels against independent phenotypic sources.

This script implements FR-010: Verify 'disease susceptibility' labels come from
independent phenotypic sources. It reads sample metadata, checks the phenotype_source
field against a whitelist of approved independent sources, and generates a linkage
method report.

Input: data/processed/sample_metadata.csv (output of T001a)
Output: data/processed/linkage_method.yaml
"""
import os
import sys
import csv
import yaml
from pathlib import Path
from typing import List, Dict, Set, Any, Tuple
from dataclasses import dataclass, asdict

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger, setup_logging_for_task, close_logging, log_info, log_warning, log_error

# Whitelist of independent phenotypic sources (FR-010)
# These are sources where disease susceptibility data is collected independently
# from genomic data generation, ensuring no circular validation.
INDEPENDENT_SOURCE_WHITELIST: Set[str] = {
    "NCBI_BioSample",
    "ENA",
    "DDBJ",
    "Phenotype_Genotype_Integration_Project",
    "Crop_Disease_Initiative",
    "Global_Plant_Pathology_Network",
    "USDA_ARS_Phenotyping",
    "IRRI_Disease_Screening",
    "CIMMYT_Wheat_Screening",
    "IITA_Soybean_Pheno",
    "SOL_genomics_Network_Phenotype",
    "Maize_Genetics_Cooperation_Service"
}

# Sources that are ambiguous or potentially dependent (to be excluded)
AMBIGUOUS_SOURCES: Set[str] = {
    "self_reported",
    "unspecified",
    "literature_citation_only",
    "derived_from_same_study",
    "simulated"
}

@dataclass
class ValidationResult:
    total_samples: int
    valid_samples: int
    excluded_samples: int
    excluded_reasons: Dict[str, int]
    unique_valid_sources: List[str]
    linkage_method: str
    validation_timestamp: str
    status: str  # "PASS" or "FAIL"

def load_sample_metadata(input_path: Path) -> List[Dict[str, Any]]:
    """Load sample metadata from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    samples = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append(row)
    
    return samples

def validate_phenotype_source(source: str) -> Tuple[bool, str]:
    """
    Validate a phenotype source against the whitelist.
    
    Returns:
        Tuple of (is_valid, reason)
    """
    if not source or source.strip() == "":
        return False, "Missing phenotype_source"
    
    source_clean = source.strip()
    
    if source_clean in AMBIGUOUS_SOURCES:
        return False, f"Ambiguous source: {source_clean}"
    
    if source_clean in INDEPENDENT_SOURCE_WHITELIST:
        return True, "Verified independent source"
    
    # Check for partial matches or variations
    for whitelisted in INDEPENDENT_SOURCE_WHITELIST:
        if whitelisted.lower() in source_clean.lower() or source_clean.lower() in whitelisted.lower():
            return True, f"Matched whitelisted source: {whitelisted}"
    
    return False, f"Source not in whitelist: {source_clean}"

def run_validation(input_path: Path, output_path: Path, logger) -> ValidationResult:
    """
    Run the label validation process.
    
    Args:
        input_path: Path to sample_metadata.csv
        output_path: Path to write linkage_method.yaml
        logger: Logger instance
    
    Returns:
        ValidationResult object
    """
    from datetime import datetime
    
    log_info(logger, f"Starting label validation for {input_path}")
    
    try:
        samples = load_sample_metadata(input_path)
    except Exception as e:
        log_error(logger, f"Failed to load sample metadata: {e}")
        raise
    
    total_samples = len(samples)
    valid_samples = 0
    excluded_samples = 0
    excluded_reasons: Dict[str, int] = {}
    unique_valid_sources: Set[str] = set()
    excluded_indices: List[int] = []
    
    log_info(logger, f"Processing {total_samples} samples")
    
    for idx, sample in enumerate(samples):
        source = sample.get('phenotype_source', '')
        is_valid, reason = validate_phenotype_source(source)
        
        if is_valid:
            valid_samples += 1
            # Normalize the source for reporting
            for whitelisted in INDEPENDENT_SOURCE_WHITELIST:
                if whitelisted.lower() in source.lower() or source.lower() in whitelisted.lower():
                    unique_valid_sources.add(whitelisted)
                    break
            else:
                unique_valid_sources.add(source)
        else:
            excluded_samples += 1
            excluded_indices.append(idx)
            excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1
            log_warning(logger, f"Sample {idx} excluded: {reason}")
    
    # Determine overall status
    if valid_samples == 0:
        status = "FAIL"
        log_error(logger, "No valid samples found with independent phenotype sources")
    elif excluded_samples > 0:
        status = "PASS_WITH_WARNINGS"
        log_warning(logger, f"Validation passed with {excluded_samples} excluded samples")
    else:
        status = "PASS"
        log_info(logger, "All samples validated successfully")
    
    # Prepare linkage method description
    linkage_method = (
        f"Phenotype labels validated against independent sources. "
        f"Accepted sources: {', '.join(sorted(unique_valid_sources))}. "
        f"Excluded {excluded_samples} samples with ambiguous or non-independent sources. "
        f"Linkage between genomic and phenotypic data established via {input_path.name}."
    )
    
    result = ValidationResult(
        total_samples=total_samples,
        valid_samples=valid_samples,
        excluded_samples=excluded_samples,
        excluded_reasons=excluded_reasons,
        unique_valid_sources=sorted(list(unique_valid_sources)),
        linkage_method=linkage_method,
        validation_timestamp=datetime.now().isoformat(),
        status=status
    )
    
    # Write output YAML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "validation_summary": {
            "total_samples": result.total_samples,
            "valid_samples": result.valid_samples,
            "excluded_samples": result.excluded_samples,
            "status": result.status
        },
        "excluded_reasons": result.excluded_reasons,
        "accepted_sources": result.unique_valid_sources,
        "linkage_method": result.linkage_method,
        "validation_timestamp": result.validation_timestamp
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
    
    log_info(logger, f"Linkage method report written to {output_path}")
    
    return result

def main():
    """Main entry point for the validation script."""
    # Setup paths
    input_path = Path("data/processed/sample_metadata.csv")
    output_path = Path("data/processed/linkage_method.yaml")
    
    # Setup logging
    logger = setup_logging_for_task("T001b_validate_labels", Path("logs"))
    
    try:
        # Run validation
        result = run_validation(input_path, output_path, logger)
        
        # Log final status
        log_info(logger, f"Validation complete. Status: {result.status}")
        log_info(logger, f"Valid samples: {result.valid_samples}/{result.total_samples}")
        
        # Exit with appropriate code
        if result.status == "FAIL":
            log_error(logger, "Validation failed - no independent sources found")
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        log_error(logger, f"Validation failed with exception: {e}")
        sys.exit(1)
    finally:
        close_logging()

if __name__ == "__main__":
    main()
