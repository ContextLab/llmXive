"""
Reference Validator for Visual Search Strategies Project.

Validates citations against primary sources by checking title overlap.
Implements FR-011: Citation validation with title overlap >= 0.7.
"""
import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher

from config import get_config
from utils.logging import get_logger


def get_logger_wrapper():
    """Get logger instance for this module."""
    return get_logger(__name__)


def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a title into lowercase words, removing punctuation.
    
    Args:
        title: The title string to tokenize.
        
    Returns:
        List of lowercase word tokens.
    """
    # Convert to lowercase and remove non-alphanumeric characters
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', title.lower())
    # Split on whitespace and filter empty strings
    tokens = [t for t in cleaned.split() if t and len(t) > 1]
    return tokens


def calculate_title_overlap(title1: str, title2: str) -> float:
    """
    Calculate the overlap score between two titles.
    
    Uses a combination of Jaccard similarity on tokens and sequence matching
    to provide a robust overlap score between 0.0 and 1.0.
    
    Args:
        title1: First title string.
        title2: Second title string.
        
    Returns:
        Float overlap score between 0.0 and 1.0.
    """
    tokens1 = set(tokenize_title(title1))
    tokens2 = set(tokenize_title(title2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Jaccard similarity
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # Sequence matcher ratio (for word order consideration)
    seq_ratio = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
    
    # Weighted combination: 60% Jaccard, 40% Sequence
    return 0.6 * jaccard + 0.4 * seq_ratio


def load_citations(citations_file: Path) -> List[Dict[str, Any]]:
    """
    Load citations from a JSON file.
    
    Args:
        citations_file: Path to the JSON file containing citations.
        
    Returns:
        List of citation dictionaries with 'title' and 'source' fields.
        
    Raises:
        FileNotFoundError: If the citations file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not citations_file.exists():
        raise FileNotFoundError(f"Citations file not found: {citations_file}")
    
    with open(citations_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'citations' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'citations' in data:
        return data['citations']
    else:
        raise ValueError(f"Invalid citations format in {citations_file}")


def load_primary_sources(sources_file: Path) -> List[Dict[str, Any]]:
    """
    Load primary source references from a JSON file.
    
    Args:
        sources_file: Path to the JSON file containing primary sources.
        
    Returns:
        List of primary source dictionaries with 'title' and 'url' fields.
        
    Raises:
        FileNotFoundError: If the sources file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not sources_file.exists():
        raise FileNotFoundError(f"Primary sources file not found: {sources_file}")
    
    with open(sources_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'sources' in data:
        return data['sources']
    else:
        raise ValueError(f"Invalid sources format in {sources_file}")


def find_best_match(citation_title: str, primary_sources: List[Dict[str, Any]], 
                   threshold: float = 0.7) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Find the best matching primary source for a citation title.
    
    Args:
        citation_title: The title of the citation to match.
        primary_sources: List of primary source dictionaries.
        threshold: Minimum overlap score to consider a match valid.
        
    Returns:
        Tuple of (matching_source_dict or None, best_overlap_score).
    """
    best_match = None
    best_score = 0.0
    
    for source in primary_sources:
        source_title = source.get('title', '')
        if not source_title:
            continue
            
        score = calculate_title_overlap(citation_title, source_title)
        if score > best_score:
            best_score = score
            best_match = source
    
    # Only return match if it meets threshold
    if best_score >= threshold:
        return best_match, best_score
    else:
        return None, best_score


def validate_citations(citations: List[Dict[str, Any]], 
                     primary_sources: List[Dict[str, Any]],
                     threshold: float = 0.7) -> Dict[str, Any]:
    """
    Validate all citations against primary sources.
    
    Args:
        citations: List of citation dictionaries to validate.
        primary_sources: List of primary source dictionaries.
        threshold: Minimum overlap score for a valid match.
        
    Returns:
        Validation report dictionary with status, matches, and unmatched citations.
    """
    logger = get_logger_wrapper()
    results = {
        'total_citations': len(citations),
        'threshold': threshold,
        'validated': 0,
        'unvalidated': 0,
        'matches': [],
        'unmatched': [],
        'errors': []
    }
    
    for i, citation in enumerate(citations):
        title = citation.get('title', '')
        if not title:
            error_msg = f"Citation {i+1} missing title field"
            results['errors'].append(error_msg)
            results['unmatched'].append({
                'citation': citation,
                'reason': 'Missing title'
            })
            results['unvalidated'] += 1
            logger.warning(error_msg)
            continue
        
        try:
            match, score = find_best_match(title, primary_sources, threshold)
            
            if match:
                results['validated'] += 1
                results['matches'].append({
                    'citation': citation,
                    'matched_source': match,
                    'overlap_score': round(score, 4)
                })
                logger.info(f"Validated citation '{title[:50]}...' with score {score:.4f}")
            else:
                results['unvalidated'] += 1
                results['unmatched'].append({
                    'citation': citation,
                    'best_score': round(score, 4),
                    'reason': f'No match above threshold {threshold} (best: {score:.4f})'
                })
                logger.warning(f"Failed to validate citation '{title[:50]}...' (best score: {score:.4f})")
                
        except Exception as e:
            error_msg = f"Error validating citation {i+1}: {str(e)}"
            results['errors'].append(error_msg)
            results['unmatched'].append({
                'citation': citation,
                'reason': str(e)
            })
            logger.error(error_msg)
    
    results['status'] = 'passed' if results['unvalidated'] == 0 else 'failed'
    return results


def save_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation report to a JSON file.
    
    Args:
        report: The validation report dictionary.
        output_path: Path where the report should be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger = get_logger_wrapper()
    logger.info(f"Validation report saved to {output_path}")


def run_reference_validation(citations_path: Optional[Path] = None,
                           sources_path: Optional[Path] = None,
                           output_path: Optional[Path] = None,
                           threshold: float = 0.7) -> Dict[str, Any]:
    """
    Main entry point for reference validation.
    
    Args:
        citations_path: Path to citations JSON file. Defaults to config.
        sources_path: Path to primary sources JSON file. Defaults to config.
        output_path: Path for output report. Defaults to config.
        threshold: Minimum overlap score for valid match.
        
    Returns:
        Validation report dictionary.
    """
    logger = get_logger_wrapper()
    config = get_config()
    
    # Use config defaults if paths not provided
    if citations_path is None:
        citations_path = config.get('citations_file', config.data_dir / 'citations.json')
    if sources_path is None:
        sources_path = config.get('primary_sources_file', config.data_dir / 'primary_sources.json')
    if output_path is None:
        output_path = config.results_dir / 'validation' / 'reference_validation_report.json'
    
    logger.info(f"Starting reference validation with threshold {threshold}")
    logger.info(f"Citations file: {citations_path}")
    logger.info(f"Primary sources file: {sources_path}")
    logger.info(f"Output file: {output_path}")
    
    # Load data
    citations = load_citations(citations_path)
    primary_sources = load_primary_sources(sources_path)
    
    logger.info(f"Loaded {len(citations)} citations and {len(primary_sources)} primary sources")
    
    # Validate
    report = validate_citations(citations, primary_sources, threshold)
    
    # Save report
    save_validation_report(report, output_path)
    
    # Log summary
    logger.info(f"Validation complete: {report['validated']}/{report['total_citations']} validated")
    if report['unvalidated'] > 0:
        logger.warning(f"{report['unvalidated']} citations failed validation")
    
    return report


def main():
    """Command-line entry point for reference validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate citations against primary sources')
    parser.add_argument('--citations', type=Path, help='Path to citations JSON file')
    parser.add_argument('--sources', type=Path, help='Path to primary sources JSON file')
    parser.add_argument('--output', type=Path, help='Path for output report')
    parser.add_argument('--threshold', type=float, default=0.7, 
                      help='Minimum overlap score for valid match (default: 0.7)')
    
    args = parser.parse_args()
    
    try:
        report = run_reference_validation(
            citations_path=args.citations,
            sources_path=args.sources,
            output_path=args.output,
            threshold=args.threshold
        )
        
        # Exit with error code if validation failed
        if report['status'] == 'failed':
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger = get_logger_wrapper()
        logger.error(f"Reference validation failed: {str(e)}")
        sys.exit(2)


if __name__ == '__main__':
    main()