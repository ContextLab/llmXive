"""
Generate citation verification report for Constitution Principle II compliance.

This module orchestrates the citation validation process and produces
a JSON report at data/output/citation_validation.json that records
the verification status of all external dataset citations.

The report must pass (all citations verified) before data ingestion begins.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Import from existing API surface
from validate.citations import (
    CitationValidationResult,
    CitationValidationReport,
    verify_url_accessible,
    verify_checksum,
    verify_required_variables,
    validate_citation,
    validate_citations,
    generate_validation_report
)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
SPEC_PATH = PROJECT_ROOT / "specs" / "001-code-generation-performance-outcomes" / "spec.md"

def load_verified_datasets_from_spec() -> List[Dict[str, Any]]:
    """
    Parse the # Verified datasets block from spec.md (T000 output).
    
    Returns list of dataset citations with URL, checksum, and required variables.
    """
    if not SPEC_PATH.exists():
        return []
    
    datasets = []
    in_verified_block = False
    current_dataset = {}
    
    with open(SPEC_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line_stripped = line.strip()
            
            if line_stripped.startswith('# Verified datasets'):
                in_verified_block = True
                continue
            
            if in_verified_block:
                if line_stripped.startswith('#') and not line_stripped.startswith('##'):
                    in_verified_block = False
                    continue
                
                if line_stripped.startswith('- URL:'):
                    if current_dataset:
                        datasets.append(current_dataset)
                    current_dataset = {'url': line_stripped.replace('- URL:', '').strip()}
                elif line_stripped.startswith('  SHA-256:'):
                    current_dataset['checksum'] = line_stripped.replace('  SHA-256:', '').strip()
                elif line_stripped.startswith('  Required variables:'):
                    current_dataset['required_variables'] = line_stripped.replace('  Required variables:', '').strip()
                elif line_stripped.startswith('  Citation:'):
                    current_dataset['citation'] = line_stripped.replace('  Citation:', '').strip()
    
    if current_dataset:
        datasets.append(current_dataset)
    
    return datasets

def generate_citation_validation_report(
    datasets: List[Dict[str, Any]],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate comprehensive citation verification report.
    
    Args:
        datasets: List of dataset citations to validate
        output_path: Path where JSON report will be written
    
    Returns:
        Validation report dictionary
    """
    validation_results = []
    all_passed = True
    
    for dataset in datasets:
        url = dataset.get('url', '')
        checksum = dataset.get('checksum', '')
        required_vars = dataset.get('required_variables', '')
        citation = dataset.get('citation', '')
        
        result = validate_citation(url, checksum, required_vars, citation)
        validation_results.append(result)
        
        if not result.passed:
            all_passed = False
    
    report = generate_validation_report(
        results=validation_results,
        all_passed=all_passed,
        timestamp=datetime.utcnow().isoformat()
    )
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report

def main():
    """Main entry point for citation validation report generation."""
    print("=" * 60)
    print("Citation Verification Report Generation (T051)")
    print("Constitution Principle II - Reference Validator")
    print("=" * 60)
    
    # Load verified datasets from spec.md
    print(f"\nLoading verified datasets from: {SPEC_PATH}")
    datasets = load_verified_datasets_from_spec()
    
    if not datasets:
        print("WARNING: No verified datasets found in spec.md")
        print("Please ensure T000 completed and added datasets to '# Verified datasets' block")
        
        # Create empty report for pipeline continuity
        empty_report = {
            "report_type": "citation_validation",
            "timestamp": datetime.utcnow().isoformat(),
            "all_passed": False,
            "total_citations": 0,
            "verified_citations": 0,
            "failed_citations": 0,
            "citations": [],
            "status": "no_datasets",
            "message": "No verified datasets found. T000 must complete first."
        }
        
        output_path = DATA_OUTPUT_DIR / "citation_validation.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(empty_report, f, indent=2)
        
        print(f"Created empty report at: {output_path}")
        print("Pipeline blocked: T000 must add verified datasets to spec.md")
        sys.exit(1)
    
    print(f"Found {len(datasets)} verified dataset(s)")
    
    # Generate validation report
    output_path = DATA_OUTPUT_DIR / "citation_validation.json"
    print(f"\nGenerating citation validation report...")
    print(f"Output: {output_path}")
    
    report = generate_citation_validation_report(datasets, output_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total citations: {report['total_citations']}")
    print(f"Verified: {report['verified_citations']}")
    print(f"Failed: {report['failed_citations']}")
    print(f"All passed: {report['all_passed']}")
    print(f"Report: {report['status']}")
    
    if report['all_passed']:
        print("\n✓ Citation validation PASSED")
        print("Pipeline can proceed to data ingestion")
        sys.exit(0)
    else:
        print("\n✗ Citation validation FAILED")
        print("Pipeline BLOCKED - fix unverified citations before proceeding")
        sys.exit(1)

if __name__ == "__main__":
    main()
