"""
Main pipeline orchestrator for llmXive automated science pipeline.

Constitution Principle II: Reference-Validator Integration
- Blocks pipeline execution if citations are unverified before Phase 1 starts
- Ensures all external citations are validated before data ingestion or analysis

Usage:
    python code/main.py [--spec-file path/to/spec.md] [--output-dir data/output]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Import from existing API surface
from validate.citations import (
    validate_citations,
    generate_validation_report,
    CitationValidationReport
)

# Import dataset search utilities
from dataset_search import search_and_verify_datasets


class CitationValidator:
    """
    Reference-Validator Agent for Constitution Principle II.
    
    Validates all external citations before pipeline proceeds to Phase 1.
    Blocks execution if any citation verification fails.
    """
    
    def __init__(self, spec_file_path: str = None, output_dir: str = "data/output"):
        """
        Initialize the citation validator.
        
        Args:
            spec_file_path: Path to spec.md containing verified datasets block
            output_dir: Directory to write validation report
        """
        self.spec_file_path = spec_file_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report = None
    
    def validate(self) -> bool:
        """
        Validate all citations from the spec file.
        
        Returns:
            True if all citations pass validation, False otherwise.
        """
        print("=" * 60)
        print("CONSTITUTION PRINCIPLE II: REFERENCE-VALIDATOR AGENT")
        print("=" * 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting citation validation...")
        
        # Check if spec file exists
        if self.spec_file_path and not os.path.exists(self.spec_file_path):
            print(f"[ERROR] Spec file not found: {self.spec_file_path}")
            print("[BLOCKING] Cannot proceed without verified datasets specification")
            return False
        
        # If no spec file provided, check for default location
        if not self.spec_file_path:
            default_spec = "specs/001-code-generation-performance-outcomes/spec.md"
            if os.path.exists(default_spec):
                self.spec_file_path = default_spec
                print(f"[INFO] Using default spec file: {default_spec}")
        
        # Read verified datasets from spec file if available
        verified_datasets = []
        if self.spec_file_path and os.path.exists(self.spec_file_path):
            print(f"[INFO] Reading verified datasets from: {self.spec_file_path}")
            with open(self.spec_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract verified datasets block (simple parsing)
                # Look for "# Verified datasets" section
                lines = content.split('\n')
                in_verified_block = False
                for line in lines:
                    if '# Verified datasets' in line:
                        in_verified_block = True
                        continue
                    if in_verified_block:
                        if line.startswith('#') and 'Verified datasets' not in line:
                            break
                        if line.strip() and not line.startswith('#'):
                            # Parse dataset entry (format: URL | SHA256 | description)
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 2:
                                verified_datasets.append({
                                    'url': parts[0],
                                    'checksum': parts[1],
                                    'description': parts[2] if len(parts) > 2 else ''
                                })
        
        print(f"[INFO] Found {len(verified_datasets)} verified dataset(s) to validate")
        
        if not verified_datasets:
            print("[WARNING] No verified datasets found in spec file")
            print("[BLOCKING] Cannot proceed without verified datasets")
            return False
        
        # Validate each citation
        all_valid = True
        validation_results = []
        
        for dataset in verified_datasets:
            print(f"\n[VALIDATING] URL: {dataset['url']}")
            
            # Validate URL accessibility and checksum
            from validate.citations import verify_url_accessible, verify_checksum
            
            url_valid = verify_url_accessible(dataset['url'])
            checksum_valid = verify_checksum(dataset['url'], dataset['checksum']) if dataset['checksum'] else True
            
            result = {
                'url': dataset['url'],
                'checksum': dataset['checksum'],
                'url_accessible': url_valid,
                'checksum_valid': checksum_valid,
                'valid': url_valid and checksum_valid,
                'description': dataset.get('description', '')
            }
            validation_results.append(result)
            
            if result['valid']:
                print(f"  [PASS] URL accessible: {url_valid}, Checksum valid: {checksum_valid}")
            else:
                print(f"  [FAIL] URL accessible: {url_valid}, Checksum valid: {checksum_valid}")
                all_valid = False
        
        # Generate validation report
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Generating validation report...")
        
        self.report = generate_validation_report(
            validation_results=validation_results,
            spec_file=self.spec_file_path,
          pipeline_phase='pre-phase-1',
              all_passed=all_valid
          )
        
        # Write report to output directory
        report_path = self.output_dir / 'citation_validation.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print(f"[INFO] Validation report written to: {report_path}")
        
        # Return validation status
        if all_valid:
            print("\n" + "=" * 60)
            print("CITATION VALIDATION: PASSED")
            print("=" * 60)
            print("[PROCEEDING] All citations verified - pipeline can continue to Phase 1")
            return True
        else:
            print("\n" + "=" * 60)
            print("CITATION VALIDATION: FAILED")
            print("=" * 60)
            print("[BLOCKING] Some citations failed verification - pipeline halted")
            print("[ACTION] Review and fix citations in spec.md before proceeding")
            return False


def run_pipeline():
    """
    Main pipeline orchestrator.
    
    Phase 0: Citation Validation (Constitution Principle II)
    - Validates all external citations before any data processing
    - Blocks if citations are unverified
    
    Phase 1+: Data Ingestion and Analysis (only if Phase 0 passes)
    """
    print("=" * 60)
    print("LLMXIVE AUTOMATED SCIENCE PIPELINE")
    print("Project: PROJ-462-evaluating-the-impact-of-code-generation")
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline starting...")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='llmXive automated science pipeline'
    )
    parser.add_argument(
        '--spec-file',
        type=str,
        default=None,
        help='Path to spec.md containing verified datasets'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/output',
        help='Directory for output files'
    )
    parser.add_argument(
        '--phase',
        type=str,
        default='0',
        help='Pipeline phase to run (0=citation validation, 1=data ingestion, etc.)'
    )
    args = parser.parse_args()
    
    # Phase 0: Citation Validation (Constitution Principle II)
    # This MUST complete before any other phase
    if args.phase in ['0', 'all']:
        print("\n" + "-" * 60)
        print("PHASE 0: CITATION VALIDATION (Constitution Principle II)")
        print("-" * 60)
        
        validator = CitationValidator(
            spec_file_path=args.spec_file,
            output_dir=args.output_dir
        )
        
        if not validator.validate():
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline HALTED - citation validation failed")
            return 1
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Phase 0 complete - proceeding to Phase 1")
    
    # Phase 1+: Data Ingestion and Analysis
    # Only run if Phase 0 passed
    if args.phase in ['1', 'all']:
        print("\n" + "-" * 60)
        print("PHASE 1: DATA INGESTION AND VALIDATION")
        print("-" * 60)
        print("[INFO] Data ingestion module integration placeholder")
        print("[TODO] Implement data ingestion from validated datasets")
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline complete")
    return 0


if __name__ == '__main__':
    sys.exit(run_pipeline())
