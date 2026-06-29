"""
Reference Validator Agent for llmXive research pipeline.
Validates that required citations are present in research documents per Constitution II.

Required citations:
- Slack 1979 (thermal conductivity temperature normalization)
- Smith et al. 2021 (R² performance target justification)

Output: data/results/reference_validation.json
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from utils.validation import setup_logger, handle_error


class ReferenceValidator:
    """Validates required citations in research documents per Constitution II."""
    
    REQUIRED_REFERENCES = [
        "Slack 1979",
        "Smith et al. 2021"
    ]
    
    REFERENCE_PATTERNS = {
        "Slack 1979": [
            r"Slack\s*\(?1979\)?",
            r"Slack,\s*1979",
            r"Slack\(1979\)",
            r"Slack et al.\s*1979",
            r"Slack, G. A.\s*1979",
            r"Slack, G.\s*1979"
        ],
        "Smith et al. 2021": [
            r"Smith\s+et\s+al\.\s*2021",
            r"Smith et al.,\s*2021",
            r"Smith\(et\s+al\.\)\s*2021",
            r"Smith et al \(2021\)",
            r"Smith, J\. et al\.\s*2021"
        ]
    }
    
    def __init__(self, project_root: Path = None):
        """
        Initialize the Reference Validator.
        
        Args:
            project_root: Path to project root (default: current directory)
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = project_root
        self.logger = setup_logger(
            name="reference_validator",
            level=logging.INFO
        )
    
    def _find_reference(self, content: str, ref_name: str) -> bool:
        """
        Search for a reference citation in document content.
        
        Args:
            content: Document text to search
            ref_name: Name of the required reference
            
        Returns:
            True if reference is found, False otherwise
        """
        patterns = self.REFERENCE_PATTERNS.get(ref_name, [])
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def validate_references(self, document_path: Path) -> Dict[str, bool]:
        """
        Validate that all required references appear in a document.
        
        Args:
            document_path: Path to the document to validate
            
        Returns:
            Dict mapping reference names to their validation status
        """
        try:
            content = document_path.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Failed to read {document_path}: {e}")
            return {ref: False for ref in self.REQUIRED_REFERENCES}
        
        results = {}
        for ref in self.REQUIRED_REFERENCES:
            found = self._find_reference(content, ref)
            results[ref] = found
            if found:
                self.logger.info(f"Found reference '{ref}' in {document_path}")
            else:
                self.logger.warning(f"Missing reference '{ref}' in {document_path}")
        
        return results
    
    def validate_all_documents(self, search_dir: Path = None) -> Dict[str, Dict[str, bool]]:
        """
        Validate references across all research documents in a directory.
        
        Args:
            search_dir: Directory to search for documents (default: data/results)
            
        Returns:
            Dict mapping document paths to their validation results
        """
        if search_dir is None:
            search_dir = self.project_root / "data" / "results"
        
        if not search_dir.exists():
            self.logger.warning(f"Search directory does not exist: {search_dir}")
            return {}
        
        results = {}
        md_files = list(search_dir.glob("*.md"))
        
        if not md_files:
            self.logger.warning(f"No markdown files found in {search_dir}")
            return {}
        
        self.logger.info(f"Found {len(md_files)} markdown files to validate")
        
        for md_file in md_files:
            file_results = self.validate_references(md_file)
            rel_path = str(md_file.relative_to(self.project_root))
            results[rel_path] = file_results
        
        return results
    
    def generate_report(self, validation_results: Dict[str, Dict[str, bool]], output_path: Path = None) -> Path:
        """
        Generate a JSON validation report.
        
        Args:
            validation_results: Results from validate_all_documents
            output_path: Path for output report (default: data/results/reference_validation.json)
            
        Returns:
            Path to the generated report
        """
        if output_path is None:
            output_path = self.project_root / "data" / "results" / "reference_validation.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        all_passed = all(
            all(status for status in doc_results.values())
            for doc_results in validation_results.values()
        ) if validation_results else False
        
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "required_references": self.REQUIRED_REFERENCES,
            "documents_validated": list(validation_results.keys()),
            "results": validation_results,
            "overall_status": "passed" if all_passed else "failed",
            "constitution_compliance": {
                "constitution_id": "II",
                "requirement": "All citations must be verified before publication",
                "compliant": all_passed
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return output_path
    
    def run(self, output_path: Path = None) -> Tuple[bool, Path]:
        """
        Execute the full validation pipeline.
        
        Args:
            output_path: Path for output report
            
        Returns:
            Tuple of (validation_passed, report_path)
        """
        self.logger.info("Starting reference validation per Constitution II")
        
        validation_results = self.validate_all_documents()
        
        if not validation_results:
            self.logger.warning("No documents were validated")
            if output_path is None:
                output_path = self.project_root / "data" / "results" / "reference_validation.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            report = {
                "validation_timestamp": datetime.now().isoformat(),
                "required_references": self.REQUIRED_REFERENCES,
                "documents_validated": [],
                "results": {},
                "overall_status": "failed",
                "error": "No documents found to validate",
                "constitution_compliance": {
                    "constitution_id": "II",
                    "requirement": "All citations must be verified before publication",
                    "compliant": False
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            return False, output_path
        
        report_path = self.generate_report(validation_results, output_path)
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        self.logger.info(f"Validation complete. Status: {report['overall_status']}")
        self.logger.info(f"Report written to: {report_path}")
        
        return report['overall_status'] == 'passed', report_path


def main():
    """Entry point for reference validation."""
    project_root = Path(__file__).parent.parent
    validator = ReferenceValidator(project_root)
    
    success, report_path = validator.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
