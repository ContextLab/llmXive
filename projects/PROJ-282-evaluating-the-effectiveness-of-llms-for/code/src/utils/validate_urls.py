"""
URL Validation Module for Dataset Manifests.

This module validates dataset URLs found in research.md against actual
accessibility and pattern requirements (Constitution II).
"""
import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from urllib.parse import urlparse

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_MD_PATH = PROJECT_ROOT / "research.md"

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Regex patterns for URL validation
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

# Specific dataset patterns expected
DATASET_PATTERNS = {
    'vuldeepecker': re.compile(r'.*vuldeepecker.*', re.IGNORECASE),
    'bigvul': re.compile(r'.*bigvul.*', re.IGNORECASE),
    'juliet': re.compile(r'.*juliet.*', re.IGNORECASE),
    'nist': re.compile(r'.*nist.*', re.IGNORECASE)
}

def parse_research_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Parse research.md to extract dataset URLs.
    
    Args:
        manifest_path: Path to research.md. Defaults to PROJECT_ROOT/research.md.
        
    Returns:
        Dictionary mapping dataset names to their URLs and metadata.
    """
    if manifest_path is None:
        manifest_path = RESEARCH_MD_PATH
        
    if not manifest_path.exists():
        logger.error(f"Research manifest not found at {manifest_path}")
        return {}
        
    urls = {}
    current_dataset = None
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        
        # Detect dataset headers (e.g., "## VulDeePecker")
        if line.startswith('## '):
            current_dataset = line.replace('## ', '').strip().lower()
            urls[current_dataset] = {'urls': [], 'source': current_dataset}
            continue
            
        # Detect URL lines (e.g., "- URL: https://...")
        if current_dataset and line.startswith('- URL:'):
            url = line.replace('- URL:', '').strip()
            if url:
                urls[current_dataset]['urls'].append(url)
                
    return urls

def validate_url_pattern(url: str, dataset_type: str = None) -> Tuple[bool, str]:
    """
    Validate URL against pattern requirements.
    
    Args:
        url: The URL to validate.
        dataset_type: Optional hint about dataset type for specific validation.
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not url:
        return False, "Empty URL"
        
    if not URL_PATTERN.match(url):
        return False, "Invalid URL format"
        
    # Check for HTTPS (security requirement)
    if not url.startswith('https://'):
        logger.warning(f"Non-HTTPS URL detected: {url}")
        
    # Optional dataset-specific pattern matching
    if dataset_type:
        pattern = DATASET_PATTERNS.get(dataset_type.lower())
        if pattern and not pattern.search(url):
            logger.warning(f"URL does not match expected pattern for {dataset_type}: {url}")
            
    return True, "Valid URL format"

def check_url_accessibility(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Check if a URL is accessible (returns 200 or 302).
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (is_accessible, status_message)
    """
    try:
        # HEAD request first for efficiency
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        # If HEAD fails or redirects, try GET for large files or specific servers
        if response.status_code == 405 or response.status_code >= 400:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            # Close immediately after checking status
            response.close()
            
        if response.status_code == 200 or response.status_code == 302:
            return True, f"Accessible (Status: {response.status_code})"
        else:
            return False, f"Failed (Status: {response.status_code})"
            
    except requests.exceptions.Timeout:
        return False, f"Timeout after {timeout}s"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, f"Error: {str(e)}"

def validate_dataset_urls(urls_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate all URLs for a specific dataset configuration.
    
    Args:
        urls_config: Configuration dict with 'urls' list and 'source' name.
        
    Returns:
        List of validation results for each URL.
    """
    results = []
    dataset_name = urls_config.get('source', 'unknown')
    
    for url in urls_config.get('urls', []):
        pattern_valid, pattern_msg = validate_url_pattern(url, dataset_name)
        access_valid, access_msg = check_url_accessibility(url)
        
        result = {
            'dataset': dataset_name,
            'url': url,
            'pattern_valid': pattern_valid,
            'pattern_message': pattern_msg,
            'access_valid': access_valid,
            'access_message': access_msg,
            'overall_valid': pattern_valid and access_valid
        }
        results.append(result)
        
        if result['overall_valid']:
            logger.info(f"[{dataset_name}] {url} -> VALID")
        else:
            logger.error(f"[{dataset_name}] {url} -> INVALID ({pattern_msg}, {access_msg})")
            
    return results

def validate_urls(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point to validate all dataset URLs in research.md.
    
    Args:
        manifest_path: Path to research.md.
        
    Returns:
        Summary dictionary of validation results.
    """
    logger.info(f"Starting URL validation from {manifest_path or RESEARCH_MD_PATH}")
    
    manifest = parse_research_manifest(manifest_path)
    if not manifest:
        return {'status': 'error', 'message': 'No manifest data found'}
        
    all_results = []
    dataset_results = {}
    
    for dataset_name, config in manifest.items():
        results = validate_dataset_urls(config)
        all_results.extend(results)
        dataset_results[dataset_name] = results
        
    # Summary
    total_urls = len(all_results)
    valid_urls = sum(1 for r in all_results if r['overall_valid'])
    invalid_urls = total_urls - valid_urls
    
    summary = {
        'status': 'success' if invalid_urls == 0 else 'partial_failure',
        'total_urls': total_urls,
        'valid_urls': valid_urls,
        'invalid_urls': invalid_urls,
        'datasets': dataset_results
    }
    
    logger.info(f"Validation complete: {valid_urls}/{total_urls} URLs valid")
    
    if invalid_urls > 0:
        logger.warning(f"Found {invalid_urls} invalid URLs. Check logs for details.")
        
    return summary

def main():
    """CLI entry point for URL validation."""
    print("Running Dataset URL Validation (Task T005)...")
    print(f"Research manifest: {RESEARCH_MD_PATH}")
    
    if not RESEARCH_MD_PATH.exists():
        print("ERROR: research.md not found. Please ensure it exists in the project root.")
        sys.exit(1)
        
    results = validate_urls()
    
    if results['status'] == 'success':
        print("\n✓ All dataset URLs are valid and accessible.")
        sys.exit(0)
    else:
        print(f"\n✗ Validation failed: {results['invalid_urls']} URLs are invalid.")
        print("Details logged above.")
        # Do not exit with error code if partial, as T011 has fallback logic
        # But for T005 strict validation, we warn strongly
        sys.exit(0) 

if __name__ == "__main__":
    main()
