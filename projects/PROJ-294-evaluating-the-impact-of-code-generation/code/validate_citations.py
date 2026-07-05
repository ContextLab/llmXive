import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from utils import get_logger, set_task_id, get_task_id

class CitationValidator:
    def __init__(self):
        self.logger = get_logger()
        self.patterns = {
            "url": r"https?://[^\s]+",
            "doi": r"10\.\d{4,9}/[-._;()/:A-Z0-9]+",
            "arxiv": r"arXiv:\d{4}\.\d{4,5}(v\d+)?"
        }

    def extract_references(self, text: str) -> Dict[str, List[str]]:
        references = {key: [] for key in self.patterns}
        for key, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            references[key] = list(set(matches))
        return references

    def validate_citation(self, citation: str, expected_format: str) -> Tuple[bool, str]:
        if expected_format == "doi":
            if re.match(self.patterns["doi"], citation):
                return True, "Valid DOI"
            return False, "Invalid DOI format"
        elif expected_format == "url":
            if re.match(self.patterns["url"], citation):
                return True, "Valid URL"
            return False, "Invalid URL format"
        elif expected_format == "arxiv":
            if re.match(self.patterns["arxiv"], citation):
                return True, "Valid ArXiv ID"
            return False, "Invalid ArXiv ID format"
        return False, "Unknown format"

    def validate_batch(self, text: str) -> Dict[str, Any]:
        """
        Main entry point for the Reference-Validator Agent.
        Extracts all references from the text and validates each one.
        Returns a structured report of valid/invalid citations.
        """
        self.logger.info(f"Validating citations in text of length {len(text)}")
        references = self.extract_references(text)
        validation_results = {}
        
        for key, refs in references.items():
            validation_results[key] = []
            for ref in refs:
                is_valid, msg = self.validate_citation(ref, key)
                entry = {
                    "reference": ref,
                    "valid": is_valid,
                    "message": msg,
                    "format_type": key
                }
                validation_results[key].append(entry)
                if not is_valid:
                    self.logger.warning(f"Invalid citation found: {ref} ({msg})")
                else:
                    self.logger.debug(f"Valid citation found: {ref}")

        # Summary statistics
        total_refs = sum(len(v) for v in validation_results.values())
        valid_refs = sum(
            sum(1 for item in v if item["valid"]) 
            for v in validation_results.values()
        )
        
        validation_results["_summary"] = {
            "total_citations": total_refs,
            "valid_citations": valid_refs,
            "invalid_citations": total_refs - valid_refs,
            "validation_rate": valid_refs / total_refs if total_refs > 0 else 0.0
        }

        return validation_results

def validate_citations(text: str) -> Dict[str, Any]:
    """
    Convenience wrapper function for the CitationValidator.
    Returns the full validation report.
    """
    set_task_id(get_task_id()) # Ensure context is set
    validator = CitationValidator()
    return validator.validate_batch(text)

if __name__ == "__main__":
    # Example usage for manual verification
    sample_text = """
    Research Paper Reference Check:
    1. Visit our repo at https://github.com/example/repo
    2. Read the paper on ArXiv: arXiv:2301.12345v2
    3. DOI reference: 10.1000/xyz123
    4. Invalid URL: http://
    5. Invalid DOI: 10.123/
    """
    
    set_task_id("T007-TEST")
    results = validate_citations(sample_text)
    
    import json
    print(json.dumps(results, indent=2))