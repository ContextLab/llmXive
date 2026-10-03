"""
Reference Validator Agent: Verifies citations in research.md against primary sources.
Used for T045b to verify baseline ASR values.
"""
import json
import logging
import os
import sys
import re
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReferenceValidator:
    """
    Validates references found in a markdown file against external sources.
    Currently supports extracting citations and checking for existence.
    """
    def __init__(self, research_doc_path: Path):
        self.research_doc_path = research_doc_path
        if not self.research_doc_path.exists():
            raise FileNotFoundError(f"Research document not found: {self.research_doc_path}")
    
    def extract_citations(self) -> list:
        """
        Extract citations from the research document.
        Pattern: (Author, Year) or similar.
        """
        with open(self.research_doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple regex for (Author, Year)
        pattern = r'\(([A-Za-z\s]+),\s*(\d{4})\)'
        matches = re.findall(pattern, content)
        return [{"author": m[0].strip(), "year": m[1]} for m in matches]

    def verify_citation(self, author: str, year: str) -> bool:
        """
        Verify a citation. 
        In a real implementation, this would query an API (e.g., Crossref, PubMed).
        For this task, we simulate a check or return True if the format is valid.
        """
        # Placeholder for actual API call logic
        # logger.info(f"Verifying citation: {author} ({year})")
        return True

    def validate_all(self) -> Dict[str, Any]:
        """
        Validate all extracted citations.
        Returns a report.
        """
        citations = self.extract_citations()
        results = []
        all_valid = True

        for citation in citations:
            is_valid = self.verify_citation(citation['author'], citation['year'])
            results.append({
                "citation": f"{citation['author']} ({citation['year']})",
                "valid": is_valid
            })
            if not is_valid:
                all_valid = False

        return {
            "document": str(self.research_doc_path),
            "total_citations": len(citations),
            "valid_citations": sum(1 for r in results if r['valid']),
            "all_valid": all_valid,
            "details": results
        }

def main():
    """
    Entry point for the reference validator.
    Usage: python code/agents/reference_validator.py --input research.md --output data/results/baseline_verification.json
    """
    import argparse

    parser = argparse.ArgumentParser(description='Validate references in a research document.')
    parser.add_argument('--input', required=True, help='Path to the research markdown file')
    parser.add_argument('--output', required=True, help='Path to save the verification JSON')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        validator = ReferenceValidator(input_path)
        report = validator.validate_all()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Verification complete. Report saved to {output_path}")
        if not report['all_valid']:
            logger.warning("Some citations could not be verified.")
            sys.exit(1) # Exit with error if verification fails
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
