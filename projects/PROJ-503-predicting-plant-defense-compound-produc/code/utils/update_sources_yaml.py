"""
Utility to update data/sources.yaml with acquisition metadata.
Used by downstream tasks (T001, T002) to record download dates and script versions.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_FILE = PROJECT_ROOT / "data" / "sources.yaml"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sources_yaml() -> Dict[str, Any]:
    """Load the sources.yaml configuration file."""
    if not SOURCES_FILE.exists():
        raise FileNotFoundError(f"Sources file not found: {SOURCES_FILE}")
    
    with open(SOURCES_FILE, 'r') as f:
        return yaml.safe_load(f)

def save_sources_yaml(data: Dict[str, Any]) -> None:
    """Save the configuration back to sources.yaml."""
    with open(SOURCES_FILE, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Updated {SOURCES_FILE}")

def update_expression_source(
    accession_id: str,
    download_date: str,
    checksum: str,
    preprocessing_script_version: str
) -> None:
    """
    Update a specific GEO expression dataset entry.
    
    Args:
        accession_id: GEO accession (e.g., GSE21857)
        download_date: ISO format date string
        checksum: SHA-256 hash of the downloaded file
        preprocessing_script_version: Version of the script used to parse
    """
    data = load_sources_yaml()
    found = False
    
    for i, source in enumerate(data['datasets']['expression']['sources']):
        if source['accession_id'] == accession_id:
            data['datasets']['expression']['sources'][i]['download_date'] = download_date
            data['datasets']['expression']['sources'][i]['download_status'] = 'completed'
            data['datasets']['expression']['sources'][i]['checksum'] = checksum
            data['datasets']['expression']['sources'][i]['preprocessing_script_version'] = preprocessing_script_version
            found = True
            logger.info(f"Updated expression source {accession_id}")
            break
    
    if not found:
        raise ValueError(f"Expression source {accession_id} not found in sources.yaml")
    
    save_sources_yaml(data)

def update_metabolite_source(
    accession_id: str,
    download_date: str,
    checksum: str,
    preprocessing_script_version: str
) -> None:
    """
    Update a specific Metabolomics Workbench dataset entry.
    
    Args:
        accession_id: MW accession (e.g., ST002565)
        download_date: ISO format date string
        checksum: SHA-256 hash of the downloaded file
        preprocessing_script_version: Version of the script used to parse
    """
    data = load_sources_yaml()
    found = False
    
    for i, source in enumerate(data['datasets']['metabolite']['sources']):
        if source['accession_id'] == accession_id:
            data['datasets']['metabolite']['sources'][i]['download_date'] = download_date
            data['datasets']['metabolite']['sources'][i]['download_status'] = 'completed'
            data['datasets']['metabolite']['sources'][i]['checksum'] = checksum
            data['datasets']['metabolite']['sources'][i]['preprocessing_script_version'] = preprocessing_script_version
            found = True
            logger.info(f"Updated metabolite source {accession_id}")
            break
    
    if not found:
        raise ValueError(f"Metabolite source {accession_id} not found in sources.yaml")
    
    save_sources_yaml(data)

def main():
    """CLI entry point for updating sources.yaml."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update sources.yaml with acquisition metadata")
    parser.add_argument('--type', choices=['expression', 'metabolite'], required=True,
                        help="Type of dataset to update")
    parser.add_argument('--id', required=True, help="Accession ID (e.g., GSE21857 or ST002565)")
    parser.add_argument('--checksum', required=True, help="SHA-256 checksum of the downloaded file")
    parser.add_argument('--script-version', required=True, help="Version of preprocessing script")
    
    args = parser.parse_args()
    
    download_date = datetime.utcnow().isoformat() + "Z"
    
    try:
        if args.type == 'expression':
            update_expression_source(args.id, download_date, args.checksum, args.script_version)
        elif args.type == 'metabolite':
            update_metabolite_source(args.id, download_date, args.checksum, args.script_version)
    except Exception as e:
        logger.error(f"Failed to update sources.yaml: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
