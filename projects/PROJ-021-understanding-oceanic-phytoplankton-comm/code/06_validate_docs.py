"""
Validate research.md and data-model.md against generated artifacts.

This script ensures that the documentation accurately reflects the 
actual implementation state and artifacts produced by the pipeline.
"""
import os
import sys
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging_config import setup_logging, get_logger
from utils.config import get_config

# Initialize logging
setup_logging(level="INFO")
logger = get_logger("doc_validator")

# Configuration
RESEARCH_MD_PATH = PROJECT_ROOT / "research.md"
DATA_MODEL_MD_PATH = PROJECT_ROOT / "data-model.md"
ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"


def load_markdown_file(path: Path) -> str:
    """Load and return contents of a markdown file."""
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_documented_artifacts(doc_content: str) -> Set[str]:
    """Extract artifact paths mentioned in documentation."""
    artifacts = set()
    lines = doc_content.split('\n')
    
    for line in lines:
        # Look for common artifact patterns
        if 'data/' in line or 'figures/' in line:
            # Extract potential file paths
            parts = line.split()
            for part in parts:
                if any(ext in part for ext in ['.nc', '.csv', '.json', '.png', '.log', '.yaml']):
                    # Normalize path
                    clean_path = part.strip('.,;:()[]{}"\'')
                    if clean_path.startswith('data/') or clean_path.startswith('figures/'):
                        artifacts.add(clean_path)
    
    return artifacts


def scan_actual_artifacts() -> Dict[str, str]:
    """Scan actual artifact directories and return path -> hash mapping."""
    artifacts = {}
    
    # Directories to scan
    scan_dirs = [ARTIFACTS_DIR, PROCESSED_DIR, LOGS_DIR]
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
            
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(PROJECT_ROOT))
                # Calculate hash
                with open(file_path, 'rb') as f:
                  file_hash = hashlib.sha256(f.read()).hexdigest()
                artifacts[rel_path] = file_hash
    
    return artifacts


def validate_documentation_consistency(
    research_content: str,
    data_model_content: str,
    actual_artifacts: Dict[str, str]
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that documentation matches actual artifacts.
    
    Returns:
      (is_valid, missing_artifacts, extra_artifacts)
    """
    errors = []
    warnings = []
    
    # Extract documented artifacts
    research_artifacts = extract_documented_artifacts(research_content)
    data_model_artifacts = extract_documented_artifacts(data_model_content)
    all_documented = research_artifacts.union(data_model_artifacts)
    
    documented_list = list(all_documented)
    actual_list = list(actual_artifacts.keys())
    
    # Check for documented artifacts that don't exist
    for doc_artifact in all_documented:
        # Normalize path for comparison
        normalized = doc_artifact.strip('/')
        found = False
        for actual in actual_list:
            if normalized in actual or actual.endswith(normalized):
                found = True
                break
        
        if not found:
            errors.append(f"Documented artifact not found: {doc_artifact}")
    
    # Check for artifacts that exist but aren't documented
    for actual in actual_list:
        if not any(actual.endswith(doc) or doc in actual for doc in all_documented):
            # Skip log files and temporary files
            if not any(skip in actual for skip in ['.log', 'temp', 'tmp']):
                warnings.append(f"Artifact exists but not documented: {actual}")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_data_model_schema_consistency(
    data_model_content: str,
    actual_artifacts: Dict[str, str]
) -> Tuple[bool, List[str]]:
    """
    Validate that data-model.md schema definitions match actual artifacts.
    """
    errors = []
    
    # Check for schema file references
    schema_files = []
    if "specs/001-phytoplankton-vlm-analysis/contracts" in data_model_content:
        schema_dir = PROJECT_ROOT / "specs" / "001-phytoplankton-vlm-analysis" / "contracts"
        if schema_dir.exists():
            for file_path in schema_dir.glob('*.yaml'):
                schema_files.append(str(file_path.relative_to(PROJECT_ROOT)))
    
    # Verify schema files exist and are valid YAML
    for schema_file in schema_files:
        schema_path = PROJECT_ROOT / schema_file
        if not schema_path.exists():
            errors.append(f"Schema file referenced but not found: {schema_file}")
            continue
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML in schema {schema_file}: {str(e)}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def generate_validation_report(
    is_valid: bool,
    doc_errors: List[str],
    doc_warnings: List[str],
    schema_errors: List[str],
    actual_artifacts: Dict[str, str]
) -> Dict[str, Any]:
    """Generate a comprehensive validation report."""
    report = {
        "validation_passed": is_valid,
        "timestamp": str(Path(__file__).parent.parent),
        "summary": {
            "total_documented": len(extract_documented_artifacts(
                load_markdown_file(RESEARCH_MD_PATH)
            ).union(extract_documented_artifacts(
                load_markdown_file(DATA_MODEL_MD_PATH)
            ))),
            "total_actual": len(actual_artifacts),
            "doc_errors": len(doc_errors),
            "doc_warnings": len(doc_warnings),
            "schema_errors": len(schema_errors)
        },
        "details": {
            "document_errors": doc_errors,
            "document_warnings": doc_warnings,
            "schema_errors": schema_errors,
            "artifacts_found": list(actual_artifacts.keys())
        }
    }
    
    return report


def main():
    """Main validation function."""
    logger.info("Starting documentation validation for PROJ-021")
    
    try:
        # Load documentation
        logger.info(f"Loading {RESEARCH_MD_PATH}")
        research_content = load_markdown_file(RESEARCH_MD_PATH)
        
        logger.info(f"Loading {DATA_MODEL_MD_PATH}")
        data_model_content = load_markdown_file(DATA_MODEL_MD_PATH)
        
        # Scan actual artifacts
        logger.info("Scanning actual artifacts")
        actual_artifacts = scan_actual_artifacts()
        logger.info(f"Found {len(actual_artifacts)} artifacts")
        
        # Validate consistency
        logger.info("Validating documentation consistency")
        is_valid, doc_errors, doc_warnings = validate_documentation_consistency(
            research_content, data_model_content, actual_artifacts
        )
        
        # Validate schema consistency
        logger.info("Validating schema consistency")
        schema_valid, schema_errors = validate_data_model_schema_consistency(
            data_model_content, actual_artifacts
        )
        
        overall_valid = is_valid and schema_valid
        
        # Generate report
        report = generate_validation_report(
            overall_valid, doc_errors, doc_warnings, schema_errors, actual_artifacts
        )
        
        # Save report
        report_path = PROJECT_ROOT / "data" / "artifacts" / "doc_validation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("DOCUMENTATION VALIDATION REPORT")
        print("="*60)
        print(f"Validation Status: {'PASSED' if overall_valid else 'FAILED'}")
        print(f"Documented Artifacts: {report['summary']['total_documented']}")
        print(f"Actual Artifacts: {report['summary']['total_actual']}")
        print(f"Document Errors: {report['summary']['doc_errors']}")
        print(f"Document Warnings: {report['summary']['doc_warnings']}")
        print(f"Schema Errors: {report['summary']['schema_errors']}")
        
        if doc_errors:
            print("\nDocument Errors:")
            for err in doc_errors:
                print(f"  - {err}")
        
        if doc_warnings:
            print("\nDocument Warnings:")
            for warn in doc_warnings:
                print(f"  - {warn}")
        
        if schema_errors:
            print("\nSchema Errors:")
            for err in schema_errors:
                print(f"  - {err}")
        
        print("="*60)
        
        return 0 if overall_valid else 1
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {str(e)}", exc_info=True)
        print(f"Validation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())