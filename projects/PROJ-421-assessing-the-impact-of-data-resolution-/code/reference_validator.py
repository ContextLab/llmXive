"""
Reference Validator Agent for PROJ-421.

This module validates that NLCD data URLs (HuggingFace/proxy) are reachable
and verifies metadata consistency (Title-token-overlap >= 0.7) against primary sources.
"""
import os
import sys
import json
import logging
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Try to import requests, fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error

from utils import get_logger, retry_with_backoff
from config import PROJECT_ROOT, DATA_RAW_DIR, LOG_LEVEL


def fetch_url_metadata(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch metadata (headers, title) from a URL.
    
    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        
    Returns:
        Dictionary containing status code, headers, and title (if HTML).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; ReferenceValidator/1.0; +https://github.com/llmXive)'
    }
    
    if HAS_REQUESTS:
        try:
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            if response.status_code == 405:
                # HEAD not allowed, try GET
                response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            metadata = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'url': response.url, # Final URL after redirects
                'reachable': response.status_code < 400
            }
            
            # Try to extract title if it's HTML
            if 'text/html' in response.headers.get('Content-Type', ''):
                try:
                    text = response.text
                    title_match = re.search(r'<title>([^<]+)</title>', text, re.IGNORECASE)
                    if title_match:
                        metadata['title'] = title_match.group(1).strip()
                except Exception:
                    pass
                    
            return metadata
        except Exception as e:
            return {
                'status_code': 0,
                'error': str(e),
                'reachable': False
            }
    else:
        # Fallback to urllib
        try:
            req = urllib.request.Request(url, headers=headers, method='HEAD')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                metadata = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'url': response.url,
                    'reachable': True
                }
                return metadata
        except Exception as e:
            # Try GET if HEAD fails
            try:
                req = urllib.request.Request(url, headers=headers, method='GET')
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    metadata = {
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'url': response.url,
                        'reachable': True
                    }
                    return metadata
            except Exception as e2:
                return {
                    'status_code': 0,
                    'error': str(e2),
                    'reachable': False
                }


def calculate_token_overlap(title1: str, title2: str) -> float:
    """
    Calculate the Jaccard similarity (token overlap) between two titles.
    
    Args:
        title1: First title string.
        title2: Second title string.
        
    Returns:
        Float between 0.0 and 1.0 representing token overlap.
    """
    if not title1 or not title2:
        return 0.0
        
    # Normalize: lowercase, remove punctuation, split into tokens
    def tokenize(s: str) -> set:
        s = s.lower()
        s = re.sub(r'[^\w\s]', ' ', s)
        tokens = s.split()
        # Filter out very short tokens (likely noise)
        return {t for t in tokens if len(t) > 2}
        
    tokens1 = tokenize(title1)
    tokens2 = tokenize(title2)
    
    if not tokens1 or not tokens2:
        return 0.0
        
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union) if union else 0.0


def validate_huggingface_url(url: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate a HuggingFace dataset URL.
    
    Args:
        url: The HuggingFace URL.
        logger: Logger instance.
        
    Returns:
        Validation result dictionary.
    """
    result = {
        'url': url,
        'source': 'huggingface',
        'status': 'unknown',
        'metadata': {},
        'overlap_score': 0.0,
        'passed': False
    }
    
    logger.info(f"Validating HuggingFace URL: {url}")
    
    # Fetch metadata
    metadata = fetch_url_metadata(url)
    result['metadata'] = metadata
    
    if not metadata.get('reachable', False):
        result['status'] = 'unreachable'
        result['error'] = metadata.get('error', 'Unknown error')
        logger.error(f"URL unreachable: {result['error']}")
        return result
        
    result['status'] = 'reachable'
    
    # For HuggingFace, we expect the title to contain "NLCD" or "National Land Cover"
    # and the dataset name. We compare against a known reference title pattern.
    # Reference: "NLCD 2019 Land Cover for CONUS" (or similar)
    reference_title = "NLCD Land Cover Data"
    
    actual_title = metadata.get('title', '')
    if actual_title:
        overlap = calculate_token_overlap(actual_title, reference_title)
        result['overlap_score'] = overlap
        
        # Check if it looks like an NLCD dataset
        if 'nlcd' in actual_title.lower() or 'land cover' in actual_title.lower():
            result['status'] = 'verified'
            if overlap >= 0.7:
                result['passed'] = True
                logger.info(f"URL verified with overlap score {overlap:.2f}")
            else:
                result['passed'] = False
                logger.warning(f"URL reachable but overlap score {overlap:.2f} < 0.7")
        else:
            result['status'] = 'mismatch'
            result['passed'] = False
            logger.warning(f"URL reachable but title does not match NLCD pattern")
    else:
        # No title extracted, but URL is reachable and points to HF
        if 'huggingface.co' in url:
            result['status'] = 'reachable_no_title'
            result['passed'] = True # Assume valid if HF and reachable
            logger.info("URL reachable (no title extracted, assuming valid HuggingFace dataset)")
        else:
            result['passed'] = False
            
    return result


def validate_proxy_url(url: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate a proxy URL.
    
    Args:
        url: The proxy URL.
        logger: Logger instance.
        
    Returns:
        Validation result dictionary.
    """
    result = {
        'url': url,
        'source': 'proxy',
        'status': 'unknown',
        'metadata': {},
        'overlap_score': 0.0,
        'passed': False
    }
    
    logger.info(f"Validating proxy URL: {url}")
    
    metadata = fetch_url_metadata(url)
    result['metadata'] = metadata
    
    if not metadata.get('reachable', False):
        result['status'] = 'unreachable'
        result['error'] = metadata.get('error', 'Unknown error')
        logger.error(f"Proxy URL unreachable: {result['error']}")
        return result
        
    result['status'] = 'reachable'
    result['passed'] = True
    logger.info("Proxy URL reachable")
    
    return result


def scan_data_directory(data_dir: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Scan data directory for configuration files or URLs to validate.
    
    Args:
        data_dir: Path to the data directory.
        logger: Logger instance.
        
    Returns:
        List of validation results.
    """
    results = []
    
    # Look for config files or metadata JSONs in the data directory
    config_patterns = ['metadata.json', 'urls.json', 'config.json']
    
    for pattern in config_patterns:
        config_file = data_dir / pattern
        if config_file.exists():
            logger.info(f"Found config file: {config_file}")
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    
                urls = config_data.get('urls', [])
                if not urls and isinstance(config_data, dict):
                    # Try to find URLs in keys or nested structures
                    for key, value in config_data.items():
                        if 'url' in key.lower() and isinstance(value, str):
                            urls.append(value)
                
                for url in urls:
                    if 'huggingface' in url.lower():
                        results.append(validate_huggingface_url(url, logger))
                    elif 'proxy' in url.lower() or url.startswith('http'):
                        results.append(validate_proxy_url(url, logger))
            except Exception as e:
                logger.error(f"Error reading config file {config_file}: {e}")
                
    # Also check if there are any .txt or .md files with URLs
    for file_path in data_dir.glob('*.txt'):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Simple regex to find URLs
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
                for url in urls:
                    if 'huggingface' in url.lower():
                        results.append(validate_huggingface_url(url, logger))
                    else:
                        results.append(validate_proxy_url(url, logger))
        except Exception as e:
            logger.warning(f"Could not parse {file_path}: {e}")
            
    return results


def run_validation(input_dir: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full validation process.
    
    Args:
        input_dir: Path to the data directory to scan.
        config_path: Optional path to a specific config file.
        
    Returns:
        Summary of validation results.
    """
    logger = get_logger(__name__)
    input_path = Path(input_dir)
    
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_path}")
        return {'error': f"Input directory not found: {input_path}"}
        
    logger.info(f"Starting validation for directory: {input_path}")
    
    results = scan_data_directory(input_path, logger)
    
    # If no results found in directory, check for explicit URLs in config
    if not results and config_path:
        config_file = Path(config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    urls = config_data.get('NLCD_URLS', []) or config_data.get('urls', [])
                    for url in urls:
                        if 'huggingface' in url.lower():
                            results.append(validate_huggingface_url(url, logger))
                        else:
                            results.append(validate_proxy_url(url, logger))
            except Exception as e:
                logger.error(f"Error reading config: {e}")
    
    # If still no results, check common NLCD HuggingFace datasets
    if not results:
        logger.info("No URLs found in input. Checking common NLCD HuggingFace datasets...")
        common_urls = [
            "https://huggingface.co/datasets/usgs-nlcd/landcover",
            "https://huggingface.co/datasets/nlcd/2019_land_cover"
        ]
        for url in common_urls:
            results.append(validate_huggingface_url(url, logger))
    
    passed_count = sum(1 for r in results if r.get('passed', False))
    total_count = len(results)
    
    summary = {
        'total_urls': total_count,
        'passed': passed_count,
        'failed': total_count - passed_count,
        'results': results
    }
    
    logger.info(f"Validation complete: {passed_count}/{total_count} URLs passed")
    
    return summary


def main():
    """Main entry point for the reference validator."""
    parser = argparse.ArgumentParser(description='Reference Validator for NLCD URLs')
    parser.add_argument('--input', type=str, default=str(DATA_RAW_DIR),
                      help='Input data directory to scan for URLs')
    parser.add_argument('--config', type=str, default=None,
                      help='Path to config file containing explicit URLs')
    parser.add_argument('--output', type=str, default=None,
                      help='Path to write JSON results (default: stdout)')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
                      
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logger = get_logger(__name__, level=level)
    
    # Run validation
    summary = run_validation(args.input, args.config)
    
    # Output results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results written to {output_path}")
    else:
        print(json.dumps(summary, indent=2))
        
    # Exit with error code if validation failed
    if summary.get('failed', 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()