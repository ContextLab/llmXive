"""
Derivation Notes Validator

Validates that docs/reproducibility/derivation_notes.md contains all four required sections
with non-empty content, as specified in FR-007 and task T046.

Sections to validate:
1. Formula citations with page/section references
2. Step-by-step transformation logic with intermediate values
3. All parameter values used
4. Justification for any non-standard choices

Exit codes:
0 - Success: all sections present with non-empty content
1 - Failure: missing or empty sections
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DerivationValidationEntry:
    """Single validation entry for a section check."""
    section_name: str
    section_id: str
    found: bool
    non_empty: bool
    content_length: int
    details: str


@dataclass
class DerivationValidationResult:
    """Overall validation result for derivation notes."""
    validation_timestamp: str
    file_path: str
    total_sections: int
    passed_sections: int
    failed_sections: List[str]
    all_passed: bool
    entries: List[DerivationValidationEntry]
    message: str


class DerivationNotesValidator:
    """Validates derivation notes document structure and content."""

    # Required sections as regex patterns (case-insensitive)
    REQUIRED_SECTIONS = [
        {
            "name": "Formula Citations with Page/Section References",
            "id": "formula_citations",
            "pattern": r"##\s*1\.\s*Formula\s+Citations\s+with\s+Page/Section\s+References",
            "min_content_length": 100
        },
        {
            "name": "Step-by-Step Transformation Logic with Intermediate Values",
            "id": "transformation_logic",
            "pattern": r"##\s*2\.\s*Step-by-Step\s+Transformation\s+Logic\s+with\s+Intermediate\s+Values",
            "min_content_length": 200
        },
        {
            "name": "All Parameter Values Used",
            "id": "parameter_values",
            "pattern": r"##\s*3\.\s*All\s+Parameter\s+Values\s+Used",
            "min_content_length": 100
        },
        {
            "name": "Justification for Non-Standard Choices",
            "id": "non_standard_justification",
            "pattern": r"##\s*4\.\s*Justification\s+for\s+Non-Standard\s+Choices",
            "min_content_length": 100
        }
    ]

    def __init__(self, docs_path: Path = None):
        """
        Initialize validator with path to docs directory.

        Args:
            docs_path: Path to docs/reproducibility directory. Defaults to
                       project root + 'docs/reproducibility'.
        """
        if docs_path is None:
            docs_path = Path(__file__).parent.parent.parent / "docs" / "reproducibility"
        self.docs_path = Path(docs_path)
        self.derivation_file = self.docs_path / "derivation_notes.md"

    def validate(self) -> DerivationValidationResult:
        """
        Validate the derivation notes document.

        Returns:
            DerivationValidationResult with validation status and details.
        """
        entries = []
        failed_sections = []

        # Check if file exists
        if not self.derivation_file.exists():
            return DerivationValidationResult(
                validation_timestamp=datetime.now().isoformat(),
                file_path=str(self.derivation_file),
                total_sections=len(self.REQUIRED_SECTIONS),
                passed_sections=0,
                failed_sections=[s["name"] for s in self.REQUIRED_SECTIONS],
                all_passed=False,
                entries=entries,
                message=f"Derivation notes file not found: {self.derivation_file}"
            )

        # Read file content
        content = self.derivation_file.read_text(encoding="utf-8")

        # Validate each required section
        for section_config in self.REQUIRED_SECTIONS:
            entry = self._validate_section(content, section_config)
            entries.append(entry)

            if not entry.found or not entry.non_empty:
                failed_sections.append(section_config["name"])

        # Determine overall result
        all_passed = len(failed_sections) == 0
        passed_count = len(self.REQUIRED_SECTIONS) - len(failed_sections)

        # Generate message
        if all_passed:
            message = "All required sections present with non-empty content."
        else:
            message = f"Failed sections: {', '.join(failed_sections)}"

        return DerivationValidationResult(
            validation_timestamp=datetime.now().isoformat(),
            file_path=str(self.derivation_file),
            total_sections=len(self.REQUIRED_SECTIONS),
            passed_sections=passed_count,
            failed_sections=failed_sections,
            all_passed=all_passed,
            entries=entries,
            message=message
        )

    def _validate_section(self, content: str, section_config: Dict) -> DerivationValidationEntry:
        """
        Validate a single section of the derivation notes.

        Args:
            content: Full document content.
            section_config: Configuration for the section to validate.

        Returns:
            DerivationValidationEntry with validation result.
        """
        name = section_config["name"]
        section_id = section_config["id"]
        pattern = section_config["pattern"]
        min_length = section_config.get("min_content_length", 100)

        # Check if section header exists
        match = re.search(pattern, content, re.IGNORECASE)
        found = match is not None

        if not found:
            return DerivationValidationEntry(
                section_name=name,
                section_id=section_id,
                found=False,
                non_empty=False,
                content_length=0,
                details=f"Section header not found: {name}"
            )

        # Extract section content (from header to next ## or end of file)
        start_pos = match.end()
        next_header = re.search(r"\n##\s+\d+\.", content[start_pos:])
        if next_header:
            section_content = content[start_pos:start_pos + next_header.start()]
        else:
            section_content = content[start_pos:]

        # Check if content is non-empty and meets minimum length
        content_stripped = section_content.strip()
        non_empty = len(content_stripped) >= min_length
        content_length = len(content_stripped)

        details = f"Section found with {content_length} characters"
        if not non_empty:
            details += f" (minimum required: {min_length})"

        return DerivationValidationEntry(
            section_name=name,
            section_id=section_id,
            found=True,
            non_empty=non_empty,
            content_length=content_length,
            details=details
        )

    def write_validation_report(self, result: DerivationValidationResult, output_path: Path = None) -> None:
        """
        Write validation result to a markdown report.

        Args:
            result: Validation result to report.
            output_path: Path for output report. Defaults to
                         docs/reproducibility/validation_status.md.
        """
        if output_path is None:
            output_path = self.docs_path / "validation_status.md"

        lines = [
            "# Derivation Notes Validation Report",
            "",
            f"**Validation Timestamp**: {result.validation_timestamp}",
            f"**File Validated**: {result.file_path}",
            "",
            "## Summary",
            "",
            f"- **Total Sections**: {result.total_sections}",
            f"- **Passed Sections**: {result.passed_sections}",
            f"- **Failed Sections**: {len(result.failed_sections)}",
            f"- **Overall Status**: {'PASS' if result.all_passed else 'FAIL'}",
            "",
            "## Section Details",
            ""
        ]

        for entry in result.entries:
            status = "✓" if (entry.found and entry.non_empty) else "✗"
            lines.append(f"### {status} {entry.section_name}")
            lines.append("")
            lines.append(f"- **Found**: {entry.found}")
            lines.append(f"- **Non-empty**: {entry.non_empty}")
            lines.append(f"- **Content Length**: {entry.content_length} characters")
            lines.append(f"- **Details**: {entry.details}")
            lines.append("")

        lines.append("## Validation Message")
        lines.append("")
        lines.append(result.message)
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by derivation_validator.py at {result.validation_timestamp}*")

        output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """
    Main entry point for derivation notes validation.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    validator = DerivationNotesValidator()
    result = validator.validate()

    # Print result to stdout
    print(f"Derivation Notes Validation: {'PASS' if result.all_passed else 'FAIL'}")
    print(f"File: {result.file_path}")
    print(f"Sections: {result.passed_sections}/{result.total_sections} passed")
    print(f"Message: {result.message}")

    # Write validation report
    validator.write_validation_report(result)
    print(f"Validation report written to: {validator.docs_path / 'validation_status.md'}")

    return 0 if result.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())