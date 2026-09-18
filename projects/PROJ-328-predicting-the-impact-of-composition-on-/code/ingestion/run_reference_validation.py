import os
import sys
import logging
from pathlib import Path
from utils.reference_validator import validate_research_md, ConstitutionError
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Run the reference validator on the draft research sources.
    
    This script implements T008b: Verify Research Sources.
    It reads the candidate sources from T008a, validates them,
    and generates research_verified.md.
    
    If verification fails or times out, it marks the state as 'provisional'
    in data/config/sources.yaml and proceeds to T009c.
    """
    logger.info("Starting Reference-Validator Agent for T008b...")
    
    try:
        # Define paths
        project_root = Path(__file__).parent.parent
        candidate_path = project_root / 'data' / 'config' / 'candidate_sources.txt'
        verified_output = project_root / 'specs' / '001-predict-solder-hardness' / 'research_verified.md'
        sources_yaml = project_root / 'data' / 'config' / 'sources.yaml'
        
        # Check if candidate file exists
        if not candidate_path.exists():
            logger.error(f"Candidate sources file not found: {candidate_path}")
            # Mark as provisional and exit
            _mark_provisional(sources_yaml)
            return 1
        
        # Run validation
        logger.info(f"Validating sources from: {candidate_path}")
        
        # Import the validation logic
        from utils.reference_validator import validate_research_md
        
        # Create a temporary markdown file from the JSON candidate list
        import json
        with open(candidate_path, 'r') as f:
            candidates = json.load(f)
        
        temp_md = project_root / 'data' / 'config' / 'temp_research.md'
        with open(temp_md, 'w') as f:
            f.write("# Candidate Research Sources\n\n")
            for item in candidates:
                citation = item.get('citation', 'Unknown Citation')
                url = item.get('url', '')
                f.write(f"- [{citation}]({url})\n")
        
        success, verified_sources = validate_research_md(temp_md, verified_output)
        
        if success:
            logger.info(f"Verification successful. {len(verified_sources)} sources verified.")
            # Update sources.yaml with verified URLs
            _update_sources_yaml(sources_yaml, verified_sources)
            return 0
        else:
            logger.warning("Verification failed or no sources verified. Marking as provisional.")
            _mark_provisional(sources_yaml)
            return 1
            
    except Exception as e:
        logger.error(f"Reference validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        # On timeout or critical failure, mark as provisional
        try:
            _mark_provisional(Path(__file__).parent.parent / 'data' / 'config' / 'sources.yaml')
        except:
            pass
        return 1

def _mark_provisional(sources_yaml_path: Path):
    """Mark sources.yaml as provisional when verification fails."""
    import yaml
    
    if sources_yaml_path.exists():
        with open(sources_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config['_verification_status'] = 'provisional'
        config['_verification_message'] = 'Verification failed or timed out. Using candidate sources as provisional.'
        
        with open(sources_yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Marked {sources_yaml_path} as provisional")
    else:
        logger.warning(f"Cannot mark provisional - sources.yaml not found: {sources_yaml_path}")

def _update_sources_yaml(sources_yaml_path: Path, verified_sources: list):
    """Update sources.yaml with verified URLs."""
    import yaml
    
    if sources_yaml_path.exists():
        with open(sources_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config['_verification_status'] = 'verified'
        config['_verified_count'] = len(verified_sources)
        
        # Update literature_pdfs with verified URLs
        if 'literature_pdfs' in config:
            verified_urls = {s['url']: s for s in verified_sources}
            updated_pdfs = []
            for pdf in config['literature_pdfs']:
                if pdf['url'] in verified_urls:
                    pdf['verified'] = True
                    updated_pdfs.append(pdf)
                else:
                    pdf['verified'] = False
                    updated_pdfs.append(pdf)
            config['literature_pdfs'] = updated_pdfs
        
        with open(sources_yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Updated {sources_yaml_path} with {len(verified_sources)} verified sources")
    else:
        logger.warning(f"Cannot update sources.yaml - file not found: {sources_yaml_path}")

if __name__ == '__main__':
    sys.exit(main())
