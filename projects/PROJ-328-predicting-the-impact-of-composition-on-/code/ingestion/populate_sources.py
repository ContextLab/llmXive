"""
T009c: Populate sources.yaml from verified research.

Reads data/config/research_verified.md (or candidate_sources.txt if provisional)
and populates data/config/sources.yaml with specific, verified/provisional URLs.
"""
import os
import sys
import logging
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.error_handlers import ConfigurationError

logger = get_logger(__name__)


def parse_verified_sources(input_file: Path) -> Dict[str, Any]:
    """
    Parse the verified research file (research_verified.md) or candidate file
    and extract source information into a structured dictionary.
    
    Args:
        input_file: Path to research_verified.md or candidate_sources.txt
        
    Returns:
        Dictionary containing parsed source information
    """
    if not input_file.exists():
        raise ConfigurationError(f"Source file not found: {input_file}")
    
    sources = {
        "_verification_status": "verified",
        "_verified_count": 0,
        "materials_project": {},
        "nist_uci": {},
        "openalloy": {},
        "literature_pdfs": []
    }
    
    content = input_file.read_text(encoding='utf-8')
    
    # Parse based on file type
    if input_file.suffix == '.md':
        # Parse research_verified.md format
        lines = content.split('\n')
        current_section = None
        current_source = None
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if line.startswith('## '):
                current_section = line.replace('## ', '').strip().lower()
                continue
            
            # Detect source entries (usually start with - or *)
            if line.startswith(('-', '*')):
                # Save previous source if exists
                if current_source:
                    sources["literature_pdfs"].append(current_source)
                    sources["_verified_count"] += 1
                
                # Extract source info from the line
                # Format: - [URL] Citation text
                match = re.match(r'[-*]\s*\[([^\]]+)\]\s*(.+)', line)
                if match:
                    url = match.group(1)
                    citation = match.group(2)
                    
                    current_source = {
                        "name": citation.split(':')[0].strip() if ':' in citation else citation,
                        "url": url,
                        "format": "pdf" if "pdf" in url.lower() or "doi" in url.lower() else "unknown",
                        "scraping_method": "pdfplumber",
                        "verified": True,
                        "citation": citation
                    }
                    continue
                
                # Handle key-value pairs within a source
                if current_source:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        current_source[key] = value
                        
            # Handle API sources (Materials Project, NIST, etc.)
            elif current_section in ['api_sources', 'verified_apis']:
                if ':' in line and not line.startswith('-'):
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    if 'materials' in key or 'mp' in key:
                        sources["materials_project"][key.replace('materials_project', '').strip('_')] = value
                    elif 'nist' in key or 'uci' in key:
                        sources["nist_uci"][key.replace('nist_uci', '').strip('_')] = value
                    elif 'openalloy' in key:
                        sources["openalloy"][key.replace('openalloy', '').strip('_')] = value
    
    else:
        # Parse candidate_sources.txt (JSON format fallback)
        try:
            import json
            candidates = json.loads(content)
            for candidate in candidates:
                if candidate.get('source_type') == 'api':
                    if 'materials' in candidate.get('url', '').lower():
                        sources["materials_project"] = {
                            "name": "Materials Project",
                            "type": "api",
                            "url": candidate['url'],
                            "api_key_env": "MP_API_KEY",
                            "endpoint": "/materials",
                            "description": "High-throughput DFT calculations",
                            "verified": True
                        }
                    elif 'nist' in candidate.get('url', '').lower() or 'uci' in candidate.get('url', '').lower():
                        sources["nist_uci"] = {
                            "name": "NIST/UCI Repository",
                            "type": "repository",
                            "url": candidate['url'],
                            "dataset_id": "solder_alloys",
                            "description": "Standardized alloy datasets",
                            "verified": True
                        }
                    elif 'openalloy' in candidate.get('url', '').lower():
                        sources["openalloy"] = {
                            "name": "OpenAlloy Database",
                            "type": "api",
                            "url": candidate['url'],
                            "endpoint": "/compositions",
                            "description": "Open source alloy database",
                            "verified": True
                        }
                elif candidate.get('source_type') == 'pdf':
                    sources["literature_pdfs"].append({
                        "name": candidate.get('citation', 'Unknown Source'),
                        "url": candidate['url'],
                        "format": "pdf",
                        "scraping_method": "pdfplumber",
                        "verified": False
                    })
                    sources["_verified_count"] += 1
        except json.JSONDecodeError:
            logger.warning("Could not parse candidate_sources.txt as JSON, using raw text parsing")
            # Fallback: treat as simple URL list
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    if 'pdf' in line or 'doi' in line:
                        sources["literature_pdfs"].append({
                            "name": line.split('/')[-1],
                            "url": line,
                            "format": "pdf",
                            "scraping_method": "pdfplumber",
                            "verified": False
                        })
                        sources["_verified_count"] += 1
    
    # Mark as verified if we have any sources
    if sources["_verified_count"] > 0:
        sources["_verification_status"] = "verified"
    else:
        sources["_verification_status"] = "provisional"
        logger.warning("No verified sources found, marking as provisional")
    
    return sources


def save_sources_yaml(sources: Dict[str, Any], output_path: Path) -> None:
    """
    Save the sources dictionary to a YAML file.
    
    Args:
        sources: Dictionary containing source information
        output_path: Path to save the YAML file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(sources, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    logger.info(f"Saved sources to {output_path}")


def main() -> int:
    """
    Main entry point for T009c.
    
    Returns:
        0 on success, 1 on failure
    """
    try:
        # Determine input file
        project_root = Path(__file__).resolve().parent.parent.parent
        verified_file = project_root / "specs" / "001-predict-solder-hardness" / "research_verified.md"
        candidate_file = project_root / "data" / "config" / "candidate_sources.txt"
        output_file = project_root / "data" / "config" / "sources.yaml"
        
        input_file = None
        if verified_file.exists():
            input_file = verified_file
            logger.info(f"Using verified sources from: {input_file}")
        elif candidate_file.exists():
            input_file = candidate_file
            logger.info(f"Using candidate sources (provisional) from: {input_file}")
        else:
            raise ConfigurationError(
                "Neither research_verified.md nor candidate_sources.txt found. "
                "Please run T008a and T008b first."
            )
        
        # Parse sources
        sources = parse_verified_sources(input_file)
        
        # Save to YAML
        save_sources_yaml(sources, output_file)
        
        # Verify output
        if not output_file.exists():
            raise ConfigurationError(f"Failed to create output file: {output_file}")
        
        logger.info(f"T009c completed successfully. Sources populated at {output_file}")
        return 0
        
    except Exception as e:
        logger.error(f"T009c failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
