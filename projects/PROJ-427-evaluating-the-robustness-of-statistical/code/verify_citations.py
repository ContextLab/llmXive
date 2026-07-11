"""
Citation verification module for the llmXive science pipeline.

This module implements a citation-verification step that checks artifacts
containing citations (e.g., README.md, docs/*.md) to ensure they are
reachable and valid. Results are stored in state/citation_log.yaml.
"""
import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import requests
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_STATE_DIR = DEFAULT_PROJECT_ROOT / "state"
DEFAULT_CITATION_LOG = DEFAULT_STATE_DIR / "citation_log.yaml"
DEFAULT_ARTIFACT_PATTERNS = [
    "README.md",
    "quickstart.md",
    "docs/*.md",
    "specs/**/*.md"
]

# Regex patterns for detecting citations
CITATION_PATTERNS = [
    # Markdown links: [text](url)
    r'\[([^\]]+)\]\((https?://[^\)]+)\)',
    # Bare URLs
    r'(https?://[^\s\]\)]+)',
    # DOI references
    r'(doi:?\s*10\.\d{4,9}/[-._;()/:A-Z0-9]+)',
]

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file if provided."""
    if config_path and config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def extract_citations(file_path: Path) -> List[Dict[str, str]]:
    """
    Extract all citations from a markdown/text file.
    
    Returns a list of dictionaries with 'source', 'url', and 'line' keys.
    """
    citations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return citations

    for line_num, line in enumerate(lines, 1):
        # Check markdown links
        for match in re.finditer(r'\[([^\]]+)\]\((https?://[^\)]+)\)', line):
          citations.append({
              'source': match.group(1),
              'url': match.group(2),
              'line': line_num,
              'file': str(file_path)
          })
        
        # Check bare URLs (excluding those already in markdown links)
        # Simple heuristic: look for http/https not preceded by ) or ]
        bare_matches = re.finditer(r'(?<![\)\]])\b(https?://[^\s\]\)]+)', line)
        for match in bare_matches:
            url = match.group(1)
            # Avoid duplicates if it was part of a markdown link
            if not any(c['url'] == url for c in citations):
                citations.append({
                    'source': 'Bare URL',
                    'url': url,
                    'line': line_num,
                    'file': str(file_path)
                })
        
        # Check DOI references
        doi_matches = re.finditer(r'(doi:?\s*10\.\d{4,9}/[-._;()/:A-Z0-9]+)', line, re.IGNORECASE)
        for match in doi_matches:
            doi = match.group(1).replace('doi:', '').strip()
            # Convert DOI to URL for verification
            doi_url = f"https://doi.org/{doi}"
            citations.append({
                'source': 'DOI',
                'url': doi_url,
                'original_doi': doi,
                'line': line_num,
                'file': str(file_path)
            })

    return citations

def verify_citation(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Verify if a citation URL is reachable.
    
    Returns a dict with 'status', 'message', and 'response_code'.
    """
    try:
        # Handle DOI redirects
        parsed = urlparse(url)
        if parsed.netloc == 'doi.org':
            # DOIs often redirect, we just check if the redirect works
            response = requests.head(url, allow_redirects=True, timeout=timeout)
        else:
            response = requests.head(url, allow_redirects=True, timeout=timeout)
        
        if response.status_code == 200:
            return {
                'status': 'reachable',
                'message': 'URL is accessible',
                'response_code': response.status_code
            }
        else:
            return {
                'status': 'mismatch',
                'message': f'URL returned status {response.status_code}',
                'response_code': response.status_code
            }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'unreachable',
            'message': str(e),
            'response_code': None
        }

def find_artifacts(project_root: Path, patterns: List[str]) -> List[Path]:
    """Find artifact files matching the given patterns."""
    artifacts = []
    for pattern in patterns:
        artifacts.extend(project_root.glob(pattern))
    return sorted(set(artifacts))

def verify_all_citations(
    project_root: Path = DEFAULT_PROJECT_ROOT,
    patterns: Optional[List[str]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to verify all citations in project artifacts.
    
    Returns a summary dict and writes results to state/citation_log.yaml.
    """
    if patterns is None:
        patterns = DEFAULT_ARTIFACT_PATTERNS
    
    if output_path is None:
        output_path = DEFAULT_CITATION_LOG

    # Ensure state directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifacts = find_artifacts(project_root, patterns)
    all_citations = []
    results = {
        'timestamp': str(Path(project_root).stat(st=0).st_mtime if Path(project_root).exists() else 0),
        'artifacts_checked': [],
        'citations': [],
        'summary': {
            'total_citations': 0,
            'reachable': 0,
            'unreachable': 0,
            'mismatch': 0
        }
    }

    for artifact in artifacts:
        logger.info(f"Checking citations in {artifact}")
        citations = extract_citations(artifact)
        results['artifacts_checked'].append(str(artifact))
        
        for citation in citations:
            citation_result = {
                'file': citation['file'],
                'line': citation['line'],
                'source': citation['source'],
                'url': citation['url'],
                'verification': verify_citation(citation['url'])
            }
            
            if 'original_doi' in citation:
                citation_result['original_doi'] = citation['original_doi']
            
            all_citations.append(citation_result)
            status = citation_result['verification']['status']
            results['summary']['total_citations'] += 1
            results['summary'][status] += 1

    results['citations'] = all_citations

    # Write results to YAML
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(results, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Citation verification complete. Results saved to {output_path}")
    logger.info(f"Summary: {results['summary']}")

    return results

def main():
    """CLI entry point for citation verification."""
    parser = argparse.ArgumentParser(
        description='Verify citations in project artifacts'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default=str(DEFAULT_PROJECT_ROOT),
        help='Path to project root directory'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(DEFAULT_CITATION_LOG),
        help='Path to output citation log'
    )

    args = parser.parse_args()
    project_root = Path(args.project_root)
    
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)

    config = load_config(Path(args.config)) if args.config else {}
    patterns = config.get('citation_patterns', DEFAULT_ARTIFACT_PATTERNS)

    results = verify_all_citations(
        project_root=project_root,
        patterns=patterns,
        output_path=Path(args.output)
    )

    # Fail if any citation is unreachable or mismatch
    if results['summary']['unreachable'] > 0 or results['summary']['mismatch'] > 0:
        logger.error("Citation verification FAILED: Found unreachable or mismatched citations")
        sys.exit(1)
    else:
        logger.info("Citation verification PASSED: All citations are reachable")
        sys.exit(0)

if __name__ == '__main__':
    main()
