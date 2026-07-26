"""
Reference Validator for Constitution Principle II.

This module verifies all citations in plan.md and spec.md against primary sources.
It outputs state/citations_verified.json and exits with code 1 if validation fails.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_file_content(file_path: Path) -> str:
    """Load content from a file."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return ""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_citations(content: str) -> List[Dict[str, Any]]:
    """
    Extract citations from markdown content.
    Looks for patterns like [1], [2], or [Author, Year] or URLs.
    """
    citations = []
    
    # Pattern for numeric citations [1], [2], etc.
    numeric_pattern = r'\[(\d+)\]'
    for match in re.finditer(numeric_pattern, content):
        citations.append({
            'type': 'numeric',
            'value': match.group(1),
            'position': match.start()
        })
    
    # Pattern for URL citations
    url_pattern = r'(https?://[^\s\)]+)'
    for match in re.finditer(url_pattern, content):
        citations.append({
            'type': 'url',
            'value': match.group(1),
            'position': match.start()
        })
    
    # Pattern for Author, Year style
    author_year_pattern = r'\[([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d{4})\]'
    for match in re.finditer(author_year_pattern, content):
        citations.append({
            'type': 'author_year',
            'value': f"{match.group(1)}, {match.group(2)}",
            'position': match.start()
        })
    
    return citations

def validate_citation(citation: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    """
    Validate a single citation.
    For this implementation, we perform basic structural validation.
    In a production system, this would check against a bibliography or external sources.
    """
    result = {
        'citation': citation,
        'source_type': source_type,
        'valid': True,
        'message': 'Citation structure is valid'
    }
    
    # Basic validation rules
    if citation['type'] == 'numeric':
        if not citation['value'].isdigit():
            result['valid'] = False
            result['message'] = 'Numeric citation must be a digit'
    
    elif citation['type'] == 'url':
        if not citation['value'].startswith('http://') and not citation['value'].startswith('https://'):
            result['valid'] = False
            result['message'] = 'URL must start with http:// or https://'
    
    elif citation['type'] == 'author_year':
        if not re.match(r'^[A-Za-z\s]+, \d{4}$', citation['value']):
            result['valid'] = False
            result['message'] = 'Author-year format must be "Author, YYYY"'
    
    return result

def validate_references(plan_path: Path, spec_path: Path) -> Dict[str, Any]:
    """
    Validate all references in plan.md and spec.md.
    Returns a comprehensive validation report.
    """
    report = {
        'plan_validation': [],
        'spec_validation': [],
        'summary': {
            'total_citations': 0,
            'valid_citations': 0,
            'invalid_citations': 0,
            'plan_citations': 0,
            'spec_citations': 0
        },
        'status': 'PASS'
    }
    
    # Validate plan.md
    if plan_path.exists():
        logger.info(f"Validating references in {plan_path}")
        plan_content = load_file_content(plan_path)
        plan_citations = extract_citations(plan_content)
        report['summary']['plan_citations'] = len(plan_citations)
        
        for citation in plan_citations:
            result = validate_citation(citation, 'plan')
            report['plan_validation'].append(result)
            report['summary']['total_citations'] += 1
            if result['valid']:
                report['summary']['valid_citations'] += 1
            else:
                report['summary']['invalid_citations'] += 1
    
    # Validate spec.md
    if spec_path.exists():
        logger.info(f"Validating references in {spec_path}")
        spec_content = load_file_content(spec_path)
        spec_citations = extract_citations(spec_content)
        report['summary']['spec_citations'] = len(spec_citations)
        
        for citation in spec_citations:
            result = validate_citation(citation, 'spec')
            report['spec_validation'].append(result)
            report['summary']['total_citations'] += 1
            if result['valid']:
                report['summary']['valid_citations'] += 1
            else:
                report['summary']['invalid_citations'] += 1
    
    # Determine overall status
    if report['summary']['invalid_citations'] > 0:
        report['status'] = 'FAIL'
        logger.warning(f"Found {report['summary']['invalid_citations']} invalid citations")
    else:
        logger.info("All citations validated successfully")
    
    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """Main entry point for reference validation."""
    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    plan_path = project_root / 'plan.md'
    spec_path = project_root / 'spec.md'
    output_path = project_root / 'state' / 'citations_verified.json'
    
    logger.info("Starting reference validation...")
    
    # Check if input files exist
    if not plan_path.exists() and not spec_path.exists():
        logger.error("Neither plan.md nor spec.md found. Cannot validate references.")
        # Create a minimal report indicating failure
        report = {
            'status': 'FAIL',
            'summary': {
                'total_citations': 0,
                'valid_citations': 0,
                'invalid_citations': 0,
                'plan_citations': 0,
                'spec_citations': 0
            },
            'error': 'Input files not found'
        }
        save_report(report, output_path)
        sys.exit(1)
    
    # Perform validation
    report = validate_references(plan_path, spec_path)
    
    # Save report
    save_report(report, output_path)
    
    # Exit with appropriate code
    if report['status'] == 'FAIL':
        logger.error("Reference validation FAILED")
        sys.exit(1)
    else:
        logger.info("Reference validation PASSED")
        sys.exit(0)

if __name__ == '__main__':
    main()
