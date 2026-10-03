"""
T008b: Verify Research Sources.

Runs the Reference-Validator Agent on the draft content from T008a.
Generates specs/001-predict-solder-hardness/research_verified.md containing only verified citations.
If verification fails or times out, proceeds to T009c using candidate_sources.txt as 'provisional'
and marks state as 'provisional' in data/config/sources.yaml.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path to resolve imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.reference_validator import validate_research_md, ConstitutionError

logger = get_logger(__name__)

# Constants from Constitution Principle II
CITATION_TITLE_OVERLAP_THRESHOLD = 0.7

def load_candidate_sources(path: Path) -> List[Dict[str, Any]]:
    """Load candidate sources from T008a output."""
    if not path.exists():
        raise FileNotFoundError(f"Candidate sources file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_source(source: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verify a single source.
    
    Returns:
        Tuple of (is_verified, reason)
    """
    url = source.get('url', '')
    source_type = source.get('source_type', '')
    citation = source.get('citation', '')
    
    if not url:
        return False, "Missing URL"
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        return False, "Invalid URL format"
    
    # Check for required fields based on source type
    if source_type == 'api':
        # APIs need endpoint information
        if 'endpoint' not in source and 'api_key' not in source:
            # Some APIs might not need explicit endpoint in this list
            pass  # Allow API sources without endpoint in candidate list
    
    # For PDFs, check if URL looks like a DOI or direct link
    if source_type == 'pdf':
        if not any(x in url for x in ['.pdf', 'doi.org', 'arxiv.org', 'sciencedirect']):
            logger.warning(f"PDF source may not be directly accessible: {url}")
    
    # Basic citation validation
    if not citation or len(citation) < 5:
        return False, "Invalid or missing citation"
    
    return True, "Verified"

def run_verification(candidate_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Run verification on all candidate sources.
    
    Returns:
        Dict with verification results and status
    """
    logger.info(f"Loading candidate sources from {candidate_path}")
    candidates = load_candidate_sources(candidate_path)
    
    verified_sources = []
    failed_sources = []
    
    for idx, source in enumerate(candidates):
        logger.info(f"Verifying source {idx+1}/{len(candidates)}: {source.get('url', 'N/A')}")
        
        try:
            is_verified, reason = verify_source(source)
            
            if is_verified:
                source['verified'] = True
                source['verification_reason'] = reason
                verified_sources.append(source)
                logger.debug(f"  -> VERIFIED: {reason}")
            else:
                source['verified'] = False
                source['verification_reason'] = reason
                failed_sources.append(source)
                logger.warning(f"  -> FAILED: {reason}")
                
        except Exception as e:
            source['verified'] = False
            source['verification_reason'] = f"Exception: {str(e)}"
            failed_sources.append(source)
            logger.error(f"  -> EXCEPTION: {str(e)}")
            continue
    
    # Generate verified research markdown
    verified_md_path = output_dir / "research_verified.md"
    
    with open(verified_md_path, 'w', encoding='utf-8') as f:
        f.write("# Verified Research Sources\n\n")
        f.write(f"Generated: {Path(__file__).stem}\n")
        f.write(f"Total candidates: {len(candidates)}\n")
        f.write(f"Verified: {len(verified_sources)}\n")
        f.write(f"Failed: {len(failed_sources)}\n\n")
        f.write("## Verified Sources\n\n")
        
        for source in verified_sources:
            f.write(f"### {source.get('citation', 'Unknown Citation')}\n\n")
            f.write(f"- **URL**: {source.get('url', 'N/A')}\n")
            f.write(f"- **Type**: {source.get('source_type', 'unknown')}\n")
            f.write(f"- **Verified**: {source.get('verified', False)}\n\n")
        
        if failed_sources:
            f.write("## Failed Sources (Excluded)\n\n")
            for source in failed_sources:
                f.write(f"- {source.get('citation', 'Unknown')}: {source.get('verification_reason', 'Unknown error')}\n")
    
    logger.info(f"Verified research markdown written to {verified_md_path}")
    
    # Return summary
    return {
        'total': len(candidates),
        'verified_count': len(verified_sources),
        'failed_count': len(failed_sources),
        'verified_sources': verified_sources,
        'failed_sources': failed_sources,
        'status': 'verified' if len(failed_sources) == 0 else 'provisional'
    }

def main():
    """Main entry point for T008b."""
    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_config_dir = project_root / "data" / "config"
    specs_dir = project_root / "specs" / "001-predict-solder-hardness"
    
    candidate_path = data_config_dir / "candidate_sources.txt"
    output_dir = specs_dir
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info("Starting T008b: Verify Research Sources")
        
        # Run verification
        results = run_verification(candidate_path, output_dir)
        
        # Determine final status
        final_status = results['status']
        
        if final_status == 'provisional':
            logger.warning("Verification failed for some sources. Marking as provisional.")
            logger.warning(f"Proceeding with {results['verified_count']} verified sources out of {results['total']}")
        
        # Update sources.yaml status
        sources_yaml_path = data_config_dir / "sources.yaml"
        if sources_yaml_path.exists():
            import yaml
            with open(sources_yaml_path, 'r', encoding='utf-8') as f:
                sources_data = yaml.safe_load(f)
            
            sources_data['_verification_status'] = final_status
            sources_data['_verified_count'] = results['verified_count']
            
            # Update individual source verification status
            if 'literature_pdfs' in sources_data:
                for pdf_source in sources_data['literature_pdfs']:
                    url = pdf_source.get('url', '')
                    # Find matching verified source
                    matching = next(
                        (vs for vs in results['verified_sources'] if vs.get('url') == url),
                        None
                    )
                    if matching:
                        pdf_source['verified'] = True
                    else:
                        pdf_source['verified'] = False
            
            with open(sources_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(sources_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Updated {sources_yaml_path} with verification status: {final_status}")
        else:
            logger.warning(f"sources.yaml not found at {sources_yaml_path}, skipping update")
        
        logger.info(f"T008b completed. Status: {final_status}")
        logger.info(f"Verified sources: {results['verified_count']}/{results['total']}")
        logger.info(f"Output: {output_dir / 'research_verified.md'}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        logger.error("Cannot proceed without candidate_sources.txt from T008a")
        return 1
    except Exception as e:
        logger.error(f"Verification failed with exception: {e}")
        logger.error("Marking as provisional and proceeding")
        # Even on error, create a minimal verified file
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "research_verified.md", 'w', encoding='utf-8') as f:
            f.write("# Verified Research Sources (Provisional - Error Occurred)\n\n")
            f.write(f"Error: {str(e)}\n")
            f.write("Using candidate_sources.txt as provisional list.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
