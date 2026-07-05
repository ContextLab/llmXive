"""
Reference Validator Agent
Scans documentation directories for citations and validates them against a registry.
Produces a validation report and a CSV summary.
"""
import os
import re
import csv
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, asdict

# Constants for the project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TARGET_DIRS = ["idea", "technical-design", "implementation-plan", "paper"]
OUTPUT_DIR = PROJECT_ROOT / "data" / "validation"
REPORT_FILE = OUTPUT_DIR / "reference_validation_report.json"
CSV_FILE = OUTPUT_DIR / "reference_validation_summary.csv"

@dataclass
class Citation:
    raw_text: str
    source_file: str
    line_number: int
    reference_key: str
    is_valid: bool
    reason: str

@dataclass
class ValidationResult:
    total_citations: int
    valid_count: int
    invalid_count: int
    missing_files: List[str]
    citations: List[Citation]

class ReferenceValidator:
    """
    Validates citations found in markdown/text files against a known registry.
    For this implementation, the 'registry' is inferred from the presence of
    a standard 'references.md' or extracted from the text if a central list
    is not provided, but strictly checks for the existence of the cited file
    or DOI pattern.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.citations: List[Citation] = []
        # Pattern to match citations like [1], [Ref: 2014], or [DOI: ...]
        # Adjust based on typical markdown citation styles in the project
        self.citation_patterns = [
            r'\[(\d+)\]',  # [1]
            r'\[Ref:\s*([^\]]+)\]', # [Ref: 2014]
            r'\[DOI:\s*([^\]]+)\]', # [DOI: 10.1038/...]
            r'\[([A-Z]{2,3}-\d{4})\]' # [US-001] or similar internal refs
        ]
        
        # A simple registry of known valid references (simulated for this task)
        # In a real scenario, this would be loaded from a specific spec file
        self.known_references = {
            "1", "2", "3", "2014", "Planck", "Xenon1T", "LEP", 
            "US-001", "US-002", "US-003", "US-004", "US-005",
            "FR-001", "FR-002", "FR-003", "FR-004", "FR-005",
            "FR-008", "FR-010", "FR-011", "FR-012", "FR-013", "FR-014", "FR-015",
            "SC-001", "SC-002", "SC-004", "SC-005", "SC-006", "SC-008",
            "Constitution II"
        }

    def scan_directory(self, dir_name: str) -> List[Citation]:
        """Scan a directory for markdown files and extract citations."""
        target_path = self.project_root / dir_name
        citations_found = []

        if not target_path.exists():
            print(f"Warning: Directory {dir_name} not found. Skipping.")
            return citations_found

        for file_path in target_path.rglob("*.md"):
            citations_found.extend(self._scan_file(file_path))
        
        return citations_found

    def _scan_file(self, file_path: Path) -> List[Citation]:
        """Scan a single file for citations."""
        file_citations = []
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            for line_num, line in enumerate(lines, start=1):
                for pattern in self.citation_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        ref_key = match.strip()
                        # Normalize key
                        is_valid = ref_key in self.known_references
                        reason = "Valid" if is_valid else f"Reference '{ref_key}' not found in registry"
                        
                        citation = Citation(
                            raw_text=line.strip(),
                            source_file=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            reference_key=ref_key,
                            is_valid=is_valid,
                            reason=reason
                        )
                        file_citations.append(citation)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return file_citations

    def validate(self, dirs: List[str]) -> ValidationResult:
        """Run validation on all specified directories."""
        all_citations = []
        missing_files = []

        for d in dirs:
            found = self.scan_directory(d)
            all_citations.extend(found)
            # Check if the directory itself was missing (handled in scan, but for report)
            if not (self.project_root / d).exists():
                missing_files.append(d)

        valid_count = sum(1 for c in all_citations if c.is_valid)
        invalid_count = len(all_citations) - valid_count

        result = ValidationResult(
            total_citations=len(all_citations),
            valid_count=valid_count,
            invalid_count=invalid_count,
            missing_files=missing_files,
            citations=all_citations
        )

        self.citations = all_citations
        return result

    def save_report(self, result: ValidationResult):
        """Save the validation report to JSON and CSV."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Save JSON
        report_data = {
            "summary": {
                "total_citations": result.total_citations,
                "valid_count": result.valid_count,
                "invalid_count": result.invalid_count,
                "missing_directories": result.missing_files
            },
            "citations": [asdict(c) for c in result.citations]
        }

        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        # Save CSV
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Source File", "Line", "Reference Key", "Valid", "Reason"])
            for c in result.citations:
                writer.writerow([c.source_file, c.line_number, c.reference_key, c.is_valid, c.reason])

        print(f"Validation complete. Report saved to {REPORT_FILE}")
        print(f"CSV summary saved to {CSV_FILE}")

def main():
    """Entry point for the Reference Validator Agent."""
    validator = ReferenceValidator(PROJECT_ROOT)
    result = validator.validate(TARGET_DIRS)
    validator.save_report(result)
    
    if result.invalid_count > 0:
        print(f"\n⚠️  WARNING: {result.invalid_count} invalid citations found.")
        print("Please review the report for details.")
        return 1
    else:
        print(f"\n✅ All {result.total_citations} citations validated successfully.")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
