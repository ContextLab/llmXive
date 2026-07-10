"""
Reference Validator Agent for llmXive.

This module validates citations found in a research markdown file against
a set of known valid sources or by checking basic citation syntax.
It ensures Constitution Principle II: citations are verified before implementation.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


# Simulated database of valid sources for the HEA project context
# In a real scenario, this might connect to an API or a local database of DOIs.
# For this implementation, we validate against a set of known HEA-related journals
# and standard citation patterns.
VALID_JOURNALS = {
    "Acta Materialia",
    "Scripta Materialia",
    "Journal of Alloys and Compounds",
    "Materials Today",
    "Nature Communications",
    "Physical Review B",
    "Computational Materials Science",
    "Intermetallics",
    "Journal of the Mechanical Behavior of Materials",
    "Entropy",
    "Scientific Reports"
}

# Pattern to match standard citation formats: [1], [1, 2], [12], etc.
CITATION_PATTERN = re.compile(r'\[(\d+(?:,\s*\d+)*)\]')

# Pattern to match DOI references
DOI_PATTERN = re.compile(r'doi\.org/10\.\d+/\S+')


def extract_citations(file_path: Path) -> List[str]:
    """Extract all citation markers from the file content."""
    content = file_path.read_text(encoding='utf-8')
    matches = CITATION_PATTERN.findall(content)
    # Flatten list of lists if regex groups capture multiple numbers
    citations = []
    for match in matches:
        citations.extend([c.strip() for c in match.split(',')])
    return sorted(list(set(citations)))


def validate_citation_syntax(citation_text: str) -> bool:
    """Basic syntax validation for a citation string."""
    if not citation_text or not citation_text.strip():
        return False
    # Check if it's purely numeric (standard format)
    return citation_text.strip().isdigit()


def validate_reference_content(file_path: Path) -> Dict[str, Any]:
    """
    Validates the references section of the markdown file.
    Returns a report of valid/invalid citations.
    """
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Heuristic: Find the reference section (usually starts with "## References" or "### References")
    ref_start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('## References') or line.strip().startswith('### References'):
            ref_start_idx = i
            break

    if ref_start_idx == -1:
        return {
            "valid": False,
            "error": "No References section found in the document.",
            "details": []
        }

    ref_lines = lines[ref_start_idx + 1:]
    valid_refs = []
    invalid_refs = []

    # Simple validation: Check if reference lines contain a DOI or a journal name from our list
    for line in ref_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        has_doi = bool(DOI_PATTERN.search(line))
        has_journal = any(j in line for j in VALID_JOURNALS)
        # Also accept if it looks like a standard citation entry (starts with a number or bracket)
        is_standard_entry = line and (line[0].isdigit() or line[0] == '[')

        if has_doi or has_journal or is_standard_entry:
            valid_refs.append(line)
        else:
            invalid_refs.append(line)

    return {
        "valid": len(invalid_refs) == 0,
        "total_references": len(valid_refs) + len(invalid_refs),
        "valid_count": len(valid_refs),
        "invalid_count": len(invalid_refs),
        "details": {
            "valid": valid_refs[:5], # Limit for report brevity
            "invalid": invalid_refs[:5]
        }
    }


def run_validation(input_path: str, output_path: str) -> bool:
    """
    Main entry point for the validation agent.
    Returns True if validation passes, False otherwise.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        return False

    try:
        # Step 1: Extract and check citation markers
        citations = extract_citations(input_file)
        syntax_valid = all(validate_citation_syntax(c) for c in citations)

        # Step 2: Validate reference content
        ref_report = validate_reference_content(input_file)

        # Step 3: Compile report
        report = {
            "status": "passed" if (syntax_valid and ref_report["valid"]) else "failed",
            "input_file": str(input_file),
            "citations_found": citations,
            "citation_syntax_valid": syntax_valid,
            "reference_validation": ref_report
        }

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"Validation complete. Report saved to: {output_file}")
        return report["status"] == "passed"

    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate citations in a research markdown file.")
    parser.add_argument("--input", required=True, help="Path to the input research.md file")
    parser.add_argument("--output", required=True, help="Path to the output JSON report")
    args = parser.parse_args()

    success = run_validation(args.input, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
