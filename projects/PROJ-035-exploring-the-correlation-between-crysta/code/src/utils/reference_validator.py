import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configure logging for the module
def setup_logger_module(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger_module(__name__)

class ReferenceValidator:
    """
    Validates citation metadata and content accuracy.
    Implements Constitution II requirements for citation verification.
    """

    def __init__(self, input_file: str, output_file: str):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.results: List[Dict] = []

    def load_citations(self) -> List[Dict]:
        """Load citations from the input JSON file."""
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('citations', [])

    def validate_citation_format(self, citation: Dict) -> Tuple[bool, str]:
        """
        Validates the basic format of a citation entry.
        Checks for required fields: title, authors, year, doi/journal.
        """
        required_fields = ['title', 'authors', 'year']
        missing = [field for field in required_fields if field not in citation or not citation[field]]
        
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        
        # Check for journal or doi
        if 'journal' not in citation and 'doi' not in citation:
            return False, "Missing journal or DOI"
        
        return True, "Format valid"

    def verify_title_token_overlap(self, citation: Dict, reference_text: str, threshold: float = 0.7) -> Tuple[bool, float]:
        """
        Verifies content accuracy by checking token overlap between citation title
        and reference text (e.g., from a report).
        
        Args:
            citation: The citation dictionary with 'title' field
            reference_text: The text from the report that should match the citation
            threshold: Minimum overlap ratio required (default 0.7)
        
        Returns:
            Tuple of (is_valid, overlap_score)
        """
        if not citation.get('title'):
            return False, 0.0

        # Normalize text: lower case, remove punctuation, split into tokens
        def normalize(text: str) -> List[str]:
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            return text.split()

        citation_tokens = set(normalize(citation['title']))
        reference_tokens = set(normalize(reference_text))

        if not citation_tokens or not reference_tokens:
            return False, 0.0

        # Calculate Jaccard similarity
        intersection = citation_tokens.intersection(reference_tokens)
        union = citation_tokens.union(reference_tokens)
        
        overlap_score = len(intersection) / len(union) if union else 0.0
        
        return overlap_score >= threshold, overlap_score

    def verify_citation(self, citation: Dict, report_text: Optional[str] = None) -> Dict:
        """
        Performs full verification of a single citation.
        """
        result = {
            'citation': citation,
            'format_valid': False,
            'format_message': '',
            'content_valid': False,
            'overlap_score': 0.0,
            'timestamp': datetime.now().isoformat()
        }

        # Format validation
        is_valid, msg = self.validate_citation_format(citation)
        result['format_valid'] = is_valid
        result['format_message'] = msg

        # Content validation (if report text provided)
        if report_text and result['format_valid']:
            is_content_valid, score = self.verify_title_token_overlap(citation, report_text)
            result['content_valid'] = is_content_valid
            result['overlap_score'] = score

        return result

    def run_validation(self, report_text: Optional[str] = None) -> Dict:
        """
        Runs validation on all citations in the input file.
        
        Args:
            report_text: Optional text from the final report to compare against
        
        Returns:
            Summary dictionary of validation results
        """
        try:
            citations = self.load_citations()
        except Exception as e:
            logger.error(f"Failed to load citations: {e}")
            return {'error': str(e), 'citations': []}

        results = []
        for citation in citations:
            verification = self.verify_citation(citation, report_text)
            results.append(verification)

        # Summary statistics
        total = len(results)
        format_passed = sum(1 for r in results if r['format_valid'])
        content_passed = sum(1 for r in results if r.get('content_valid', False))

        summary = {
            'total_citations': total,
            'format_valid_count': format_passed,
            'content_valid_count': content_passed,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }

        return summary

    def save_results(self, summary: Dict) -> None:
        """Saves validation results to the output file."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Validation results saved to {self.output_file}")

    def generate_log_report(self, summary: Dict) -> str:
        """
        Generates a human-readable log report from the validation summary.
        """
        lines = [
            f"Citation Verification Report",
            f"Generated: {summary['timestamp']}",
            f"Total Citations: {summary['total_citations']}",
            f"Format Valid: {summary['format_valid_count']}/{summary['total_citations']}",
            f"Content Valid: {summary['content_valid_count']}/{summary['total_citations']}",
            f"",
            f"Details:"
        ]

        for i, result in enumerate(summary['results'], 1):
            citation = result['citation']
            lines.append(f"\n{i}. {citation.get('title', 'Unknown Title')}")
            lines.append(f"   Authors: {citation.get('authors', 'N/A')}")
            lines.append(f"   Year: {citation.get('year', 'N/A')}")
            lines.append(f"   Format Valid: {result['format_valid']} - {result['format_message']}")
            
            if 'content_valid' in result:
                lines.append(f"   Content Valid: {result['content_valid']} (Overlap: {result['overlap_score']:.2f})")

        return "\n".join(lines)


def main():
    """CLI entry point for reference validation."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate research citations')
    parser.add_argument('--input', required=True, help='Input JSON file containing citations')
    parser.add_argument('--output', required=True, help='Output JSON file for results')
    parser.add_argument('--report-text', help='Optional text from final report for content verification')
    parser.add_argument('--threshold', type=float, default=0.7, help='Token overlap threshold (default: 0.7)')
    
    args = parser.parse_args()

    validator = ReferenceValidator(args.input, args.output)
    
    # Load report text if provided
    report_text = None
    if args.report_text and Path(args.report_text).exists():
        with open(args.report_text, 'r', encoding='utf-8') as f:
            report_text = f.read()

    summary = validator.run_validation(report_text)
    validator.save_results(summary)

    # Generate and print human-readable log
    log_report = validator.generate_log_report(summary)
    print(log_report)

    # Exit with error if any critical validations failed
    if summary['format_valid_count'] < summary['total_citations']:
        sys.exit(1)


if __name__ == '__main__':
    main()
