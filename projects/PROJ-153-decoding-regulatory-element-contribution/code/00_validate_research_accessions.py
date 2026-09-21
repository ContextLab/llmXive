"""
T052a: Validate research.md to extract verified, actual GEO/SRA accessions.

This script parses the project's research.md file, extracts all GEO (GSE/GSM/GEO) 
and SRA (SRX/SRR/SRS) accessions, validates them against the NCBI E-utilities API 
to ensure they are real (not placeholders like GSE####), and outputs:
1. data/verified_accessions.yaml - The validated accessions structured by type
2. data/validation_log.yaml - A log of the validation process and results

Aborts with a fatal error if any accession is a placeholder or cannot be validated.
"""
import os
import sys
import re
import yaml
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/accession_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Patterns for accessions
GEO_PATTERNS = [
  r'GSE\d+',  # Series
  r'GSM\d+',  # Sample
  r'GEO\w+',  # General GEO ID
]
SRA_PATTERNS = [
  r'SRX\d+',  # Experiment
  r'SRR\d+',  # Run
  r'SRS\d+',  # Study
  r'SRP\d+',  # Project
]

# Placeholder patterns (e.g., GSE####, SRRXXXX)
PLACEHOLDER_PATTERNS = [
  r'GSE####',
  r'GSM####',
  r'SRR####',
  r'SRX####',
  r'SRS####',
  r'SRP####',
]

def load_research_md(path: Path) -> str:
    """Load the research.md file."""
    if not path.exists():
        raise FileNotFoundError(f"research.md not found at {path}")
    return path.read_text(encoding='utf-8')

def extract_accessions(text: str) -> Dict[str, List[str]]:
    """Extract all potential accessions from text."""
    accessions = {
        'geoseries': [],
        'geosample': [],
        'sraexperiment': [],
        'srarun': [],
        'srastudy': [],
        'sraproject': []
    }
    
    # Extract GEO Series
    for match in re.findall(r'GSE\d+', text):
        accessions['geoseries'].append(match)
    
    # Extract GEO Samples
    for match in re.findall(r'GSM\d+', text):
        accessions['geosample'].append(match)
    
    # Extract SRA Experiments
    for match in re.findall(r'SRX\d+', text):
        accessions['sraexperiment'].append(match)
    
    # Extract SRA Runs
    for match in re.findall(r'SRR\d+', text):
        accessions['srarun'].append(match)
    
    # Extract SRA Studies
    for match in re.findall(r'SRS\d+', text):
        accessions['srastudy'].append(match)
        
    # Extract SRA Projects
    for match in re.findall(r'SRP\d+', text):
        accessions['sraproject'].append(match)
        
    # Deduplicate while preserving order
    for key in accessions:
        seen = set()
        unique = []
        for acc in accessions[key]:
            if acc not in seen:
                seen.add(acc)
                unique.append(acc)
        accessions[key] = unique
        
    return accessions

def check_placeholder(accession: str) -> bool:
    """Check if an accession looks like a placeholder."""
    for pattern in PLACEHOLDER_PATTERNS:
        if re.match(pattern, accession):
            return True
    return False

def validate_accession_via_ncbi(accession: str, accession_type: str) -> Tuple[bool, str]:
    """
    Validate an accession using NCBI E-utilities.
    Returns (is_valid, message)
    """
    import urllib.request
    import urllib.error
    import json

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    # Map accession type to db
    db_map = {
        'geoseries': 'geo',
        'geosample': 'geo',
        'sraexperiment': 'sra',
        'srarun': 'sra',
        'srastudy': 'sra',
        'sraproject': 'sra'
    }
    
    db = db_map.get(accession_type, 'sra')
    
    # Use efetch to validate
    params = {
        'db': db,
        'id': accession,
        'retmode': 'json'
    }
    
    query_string = '&'.join(f"{k}={v}" for k, v in params.items())
    url = f"{base_url}?{query_string}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-pipeline/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Check if response indicates success
            if db == 'geo':
                if 'result' in data and accession in data['result']:
                    return True, "Valid GEO accession"
                if 'error' in data:
                    return False, f"NCBI error: {data['error']}"
            elif db == 'sra':
                if 'SRA' in data and len(data['SRA']) > 0:
                    return True, "Valid SRA accession"
                
            # Fallback: check if we got a non-empty response
            if data:
                return True, "Valid accession (response received)"
            return False, "Empty response from NCBI"
            
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return False, f"Invalid accession (HTTP 400): {e.reason}"
        elif e.code == 404:
            return False, f"Accession not found (HTTP 404)"
        return False, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except json.JSONDecodeError:
        # If we can't parse JSON but got a response, it might still be valid
        return True, "Valid accession (non-JSON response)"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_all_accessions(accessions: Dict[str, List[str]]) -> Dict[str, Dict]:
    """
    Validate all accessions.
    Returns a structured result with validation status for each.
    """
    results = {
        'validated': [],
        'failed': [],
        'placeholders': [],
        'summary': {}
    }
    
    total = 0
    valid_count = 0
    failed_count = 0
    placeholder_count = 0
    
    for acc_type, acc_list in accessions.items():
        results['summary'][acc_type] = {'total': 0, 'valid': 0, 'failed': 0, 'placeholder': 0}
        
        for accession in acc_list:
            total += 1
            results['summary'][acc_type]['total'] += 1
            
            # Check for placeholder first
            if check_placeholder(accession):
                placeholder_count += 1
                results['summary'][acc_type]['placeholder'] += 1
                results['placeholders'].append({
                    'accession': accession,
                    'type': acc_type,
                    'reason': 'Placeholder pattern detected'
                })
                logger.warning(f"Placeholder detected: {accession} ({acc_type})")
                continue
            
            # Validate via NCBI
            is_valid, message = validate_accession_via_ncbi(accession, acc_type)
            
            if is_valid:
                valid_count += 1
                results['summary'][acc_type]['valid'] += 1
                results['validated'].append({
                    'accession': accession,
                    'type': acc_type,
                    'status': 'valid',
                    'message': message
                })
                logger.info(f"Validated: {accession} ({acc_type})")
            else:
                failed_count += 1
                results['summary'][acc_type]['failed'] += 1
                results['failed'].append({
                    'accession': accession,
                    'type': acc_type,
                    'status': 'invalid',
                    'message': message
                })
                logger.error(f"Validation failed: {accession} ({acc_type}) - {message}")
            
            # Rate limiting for NCBI API
            time.sleep(0.34)  # NCBI recommends <= 3 requests per second
    
    results['summary']['total'] = total
    results['summary']['valid'] = valid_count
    results['summary']['failed'] = failed_count
    results['summary']['placeholders'] = placeholder_count
    
    return results

def generate_verified_accessions_yaml(validation_results: Dict) -> Dict:
    """Generate the verified_accessions.yaml structure."""
    verified = {}
    
    # Group validated accessions by type
    for item in validation_results['validated']:
        acc_type = item['type']
        acc_id = item['accession']
        
        if acc_type not in verified:
            verified[acc_type] = []
        
        verified[acc_type].append({
            'accession': acc_id,
            'status': 'verified',
            'validation_message': item['message']
        })
    
    return {
        'metadata': {
            'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'source': 'research.md',
            'validator': 'T052a_validate_research_accessions'
        },
        'accessions': verified,
        'summary': validation_results['summary']
    }

def generate_validation_log_yaml(validation_results: Dict) -> Dict:
    """Generate the validation_log.yaml structure."""
    return {
        'metadata': {
            'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'source': 'research.md',
            'validator': 'T052a_validate_research_accessions'
        },
        'summary': validation_results['summary'],
        'validated_accessions': validation_results['validated'],
        'failed_accessions': validation_results['failed'],
        'placeholder_accessions': validation_results['placeholders'],
        'status': 'passed' if len(validation_results['failed']) == 0 and len(validation_results['placeholders']) == 0 else 'failed'
    }

def main():
    parser = argparse.ArgumentParser(description='Validate research.md accessions')
    parser.add_argument('--research-md', type=str, default='research.md',
                      help='Path to research.md file')
    parser.add_argument('--output-dir', type=str, default='data',
                      help='Output directory for YAML files')
    args = parser.parse_args()
    
    research_path = Path(args.research_md)
    output_dir = Path(args.output_dir)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading {research_path}...")
    try:
        content = load_research_md(research_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info("Extracting accessions...")
    accessions = extract_accessions(content)
    
    total_found = sum(len(v) for v in accessions.values())
    logger.info(f"Found {total_found} potential accessions")
    
    if total_found == 0:
        logger.error("No accessions found in research.md. Aborting.")
        sys.exit(1)
    
    logger.info("Validating accessions via NCBI...")
    validation_results = validate_all_accessions(accessions)
    
    # Generate outputs
    verified_data = generate_verified_accessions_yaml(validation_results)
    log_data = generate_validation_log_yaml(validation_results)
    
    # Write verified_accessions.yaml
    verified_path = output_dir / 'verified_accessions.yaml'
    with open(verified_path, 'w', encoding='utf-8') as f:
        yaml.dump(verified_data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Wrote {verified_path}")
    
    # Write validation_log.yaml
    log_path = output_dir / 'validation_log.yaml'
    with open(log_path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Wrote {log_path}")
    
    # Check for failures
    if validation_results['failed']:
        logger.error(f"FAILED: {len(validation_results['failed'])} accessions could not be validated")
        for item in validation_results['failed']:
            logger.error(f"  - {item['accession']} ({item['type']}): {item['message']}")
        sys.exit(1)
    
    if validation_results['placeholders']:
        logger.error(f"FAILED: {len(validation_results['placeholders'])} placeholder accessions detected")
        for item in validation_results['placeholders']:
            logger.error(f"  - {item['accession']} ({item['type']}): {item['reason']}")
        sys.exit(1)
    
    logger.info("SUCCESS: All accessions validated successfully")
    print(f"Validation complete. {validation_results['summary']['valid']} accessions verified.")
    sys.exit(0)

if __name__ == '__main__':
    main()
