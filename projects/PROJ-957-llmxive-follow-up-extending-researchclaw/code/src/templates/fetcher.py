"""
Template Fetcher for ResearchClawBench.

This module implements the logic to fetch content from a verified template URL,
extract the protocol content, and save it to a normalized markdown file.

Dependencies:
- T009a: Must have produced assets/templates/verified_template_url.txt
"""
import os
import sys
import re
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logging, log_with_context, get_global_error_tracker

# Configure logging
logger = setup_logging("template_fetcher")
error_tracker = get_global_error_tracker()

def read_verified_url(url_path: str) -> str:
    """Read the verified URL from the file produced by T009a."""
    full_path = Path(url_path)
    if not full_path.is_absolute():
        full_path = Path(__file__).resolve().parent.parent.parent / url_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"Verified URL file not found: {full_path}. "
                              "Ensure T009a has completed successfully.")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        url = f.read().strip()
    
    if not url:
        raise ValueError("Verified URL file is empty.")
    
    logger.info(f"Read verified URL: {url}")
    return url

def fetch_url_content(url: str, timeout: int = 30) -> str:
    """Fetch content from the URL."""
    logger.info(f"Fetching content from: {url}")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        error_tracker.add_error(f"Failed to fetch URL {url}: {str(e)}")
        raise RuntimeError(f"Failed to fetch URL: {str(e)}")

def extract_protocol_content(html_content: str) -> Optional[str]:
    """
    Extract protocol content from HTML.
    
    Tries multiple strategies in order:
    1. Content within <div class="protocol">
    2. Content within <section class="protocol">
    3. Content between <!-- PROTOCOL START --> and <!-- PROTOCOL END -->
    4. Content within <pre> tags if no other pattern found
    5. Fallback: extract all text content
    """
    # Strategy 1: Look for div with class "protocol"
    protocol_match = re.search(r'<div\s+[^>]*class\s*=\s*["\']protocol["\'][^>]*>(.*?)</div>', 
                             html_content, re.DOTALL | re.IGNORECASE)
    if protocol_match:
        logger.info("Found protocol content in <div class='protocol'>")
        return protocol_match.group(1)
    
    # Strategy 2: Look for section with class "protocol"
    protocol_match = re.search(r'<section\s+[^>]*class\s*=\s*["\']protocol["\'][^>]*>(.*?)</section>', 
                             html_content, re.DOTALL | re.IGNORECASE)
    if protocol_match:
        logger.info("Found protocol content in <section class='protocol'>")
        return protocol_match.group(1)
    
    # Strategy 3: Look for comment markers
    protocol_match = re.search(r'<!--\s*PROTOCOL\s+START\s*-->(.*?)<!--\s*PROTOCOL\s+END\s*-->', 
                             html_content, re.DOTALL | re.IGNORECASE)
    if protocol_match:
        logger.info("Found protocol content between PROTOCOL markers")
        return protocol_match.group(1)
    
    # Strategy 4: Look for <pre> tags (often used for code/protocol)
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', html_content, re.DOTALL | re.IGNORECASE)
    if pre_match:
        logger.info("Found protocol content in <pre> tag")
        return pre_match.group(1)
    
    # Strategy 5: Fallback - extract all text and clean up
    logger.warning("No specific protocol container found, using fallback text extraction")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    return text

def clean_html_tags(content: str) -> str:
    """Remove HTML tags and clean up the content."""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', content)
    
    # Normalize whitespace
    clean = re.sub(r'\n\s*\n', '\n\n', clean)
    clean = clean.strip()
    
    return clean

def save_protocol_content(content: str, output_path: str) -> None:
    """Save the extracted protocol content to a markdown file."""
    full_path = Path(output_path)
    
    # Create parent directories if they don't exist
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content with UTF-8 encoding
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Saved protocol content to: {full_path}")

def main():
    """Main entry point for the template fetcher."""
    logger.info("Starting template fetcher (T009b)")
    
    try:
        # Step 1: Read verified URL
        url_path = "assets/templates/verified_template_url.txt"
        url = read_verified_url(url_path)
        
        # Step 2: Fetch content
        html_content = fetch_url_content(url)
        
        # Step 3: Extract protocol content
        protocol_content = extract_protocol_content(html_content)
        
        if not protocol_content:
            error_tracker.add_error("Failed to extract protocol content from HTML")
            raise RuntimeError("Failed to extract protocol content")
        
        # Step 4: Clean HTML tags
        cleaned_content = clean_html_tags(protocol_content)
        
        # Step 5: Save to output file
        output_path = "assets/templates/TEMPLATE-001-v1.0.md"
        save_protocol_content(cleaned_content, output_path)
        
        logger.info("Template fetcher completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Template fetcher failed: {str(e)}")
        error_tracker.add_error(f"Template fetcher error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
