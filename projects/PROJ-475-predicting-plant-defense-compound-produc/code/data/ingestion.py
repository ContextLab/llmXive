"""
Data Ingestion Module for Plant Defense Compound Prediction Project.

This module handles the fetching of genomic, environmental, and compound data
from verified public sources (NCBI SRA, WorldClim/GBIF, ChemBank/PhenolExplorer)
or generates deterministic mock data if verified URLs are not configured or
accessible.

It enforces FR-001, FR-002, FR-003 constraints regarding verified URLs and
fallback mechanisms.
"""
import json
import os
import sys
import requests
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Union

# Local imports based on API surface
# Note: config module structure assumed based on provided API surface
try:
    from config import get_config, ConfigError
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_config, ConfigError

try:
    from utils.io import check_disk_space, DiskSpaceError
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.io import check_disk_space, DiskSpaceError

try:
    from data.mock_generator import (
        generate_mock_genomic_data,
        generate_mock_environmental_data,
        generate_mock_compound_data
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from mock_generator import (
        generate_mock_genomic_data,
        generate_mock_environmental_data,
        generate_mock_compound_data
    )

try:
    from utils.logging import get_module_logger
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logging import get_module_logger

# Initialize logger
logger = get_module_logger(__name__)
config = get_config()

# Constants
RAW_DATA_DIR = Path("data/raw")
ESTIMATED_SIZE_MB = 50  # Conservative estimate for environmental metadata

def fetch_url_content(url: str, timeout: int = 30) -> Union[Dict[str, Any], str]:
    """
    Fetch content from a URL.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON dict if content-type is application/json, else raw text.

    Raises:
        requests.RequestException: If the request fails.
    """
    logger.info(f"Fetching content from: {url}")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return response.json()
        else:
            return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise

def parse_vcf_content(vcf_content: str) -> Dict[str, Any]:
    """
    Parse VCF content into a structured dictionary.
    
    Since we cannot use cyvcf2 here without a full VCF file, we perform a basic
    parsing of the header and a sample of data lines to create a representative
    JSON structure. In a real production scenario, cyvcf2 would be used.

    Args:
        vcf_content: Raw VCF file content as string.

    Returns:
        Dictionary representing the VCF data.
    """
    logger.info("Parsing VCF content (basic parsing for JSON representation)")
    parsed_data = {
        "header": [],
        "variants": [],
        "metadata": {
            "format": "VCF",
            "source": "NCBI SRA (Simulated Parse)",
            "variant_count": 0
        }
    }

    lines = vcf_content.split('\n')
    variant_count = 0
    
    for line in lines:
        if line.startswith('#'):
            if line.startswith('##'):
                parsed_data["header"].append(line)
            elif line.startswith('#CHROM'):
                parsed_data["header"].append(line)
        else:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 8:
                    variant = {
                        "chrom": parts[0],
                        "pos": parts[1],
                        "id": parts[2],
                        "ref": parts[3],
                        "alt": parts[4],
                        "qual": parts[5],
                        "filter": parts[6],
                        "info": parts[7]
                    }
                    parsed_data["variants"].append(variant)
                    variant_count += 1
                    
                    # Limit variants for JSON size if needed, but keep some
                    if variant_count > 1000:
                        break

    parsed_data["metadata"]["variant_count"] = variant_count
    return parsed_data

def fetch_genomic_data(output_path: Optional[Path] = None) -> Path:
    """
    Fetch genomic data from verified URL or generate mock data.

    Args:
        output_path: Optional path to save the data. Defaults to data/raw/genomic_vcf.json.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "genomic_vcf.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = get_config()
    verified_urls = config.get('verified_urls', {})
    genomic_url = verified_urls.get('genomic')
    
    data = None
    source = "unknown"

    if genomic_url:
        try:
            logger.info(f"Attempting to fetch genomic data from verified URL: {genomic_url}")
            content = fetch_url_content(genomic_url)
            
            # If it's a VCF file (text), parse it. If it's already JSON, use it.
            if isinstance(content, str):
                # Check if it looks like VCF
                if content.startswith('##'):
                    data = parse_vcf_content(content)
                else:
                    # Assume it's JSON text
                    data = json.loads(content)
            else:
                data = content
            
            source = "Real Data (Verified URL)"
            logger.info("Successfully fetched real genomic data.")
            
        except Exception as e:
            logger.warning(f"Failed to fetch real genomic data: {e}. Falling back to mock data.")
            source = "Mock Data (Fallback)"
            data = generate_mock_genomic_data()
    else:
        logger.info("No verified genomic URL configured. Generating mock data.")
        source = "Mock Data (No Config)"
        data = generate_mock_genomic_data()

    # Save data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Genomic data saved to {output_path} (Source: {source})")
    
    # Post-check: Verify disk usage
    try:
        check_disk_space(ESTIMATED_SIZE_MB * 1024 * 1024)
        logger.info("Disk space check passed after genomic data ingestion.")
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

    return output_path

def fetch_env_data(output_path: Optional[Path] = None) -> Path:
    """
    Fetch environmental metadata from verified WorldClim/GBIF URL OR generate mock data.
    
    Explicitly enforces verified URL check before fallback to mock to preserve FR-002 constraint.

    Args:
        output_path: Optional path to save the data. Defaults to data/raw/env_data.json.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "env_data.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = get_config()
    verified_urls = config.get('verified_urls', {})
    env_url = verified_urls.get('env')
    
    data = None
    source = "unknown"

    if env_url:
        try:
            logger.info(f"Attempting to fetch environmental data from verified URL: {env_url}")
            content = fetch_url_content(env_url)
            
            if isinstance(content, str):
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # If not JSON, treat as raw text and wrap in a structure
                    data = {"raw_content": content, "format": "text"}
            else:
                data = content
            
            source = "Real Data (Verified URL)"
            logger.info("Successfully fetched real environmental data.")
            
        except Exception as e:
            logger.warning(f"Failed to fetch real environmental data: {e}. Falling back to mock data.")
            source = "Mock Data (Fallback)"
            data = generate_mock_environmental_data()
    else:
        logger.info("No verified environmental URL configured. Generating mock data.")
        source = "Mock Data (No Config)"
        data = generate_mock_environmental_data()

    # Save data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Environmental data saved to {output_path} (Source: {source})")
    
    # Post-check: Verify disk usage (T008)
    try:
        check_disk_space(ESTIMATED_SIZE_MB * 1024 * 1024)
        logger.info("Disk space check passed after environmental data ingestion.")
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

    return output_path

def fetch_compound_data(output_path: Optional[Path] = None) -> Path:
    """
    Fetch defense compound profiles from verified ChemBank/PhenolExplorer URL OR generate mock data.
    
    Explicitly enforces verified URL check before fallback to mock to preserve FR-003 constraint.

    Args:
        output_path: Optional path to save the data. Defaults to data/raw/compound_data.json.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "compound_data.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = get_config()
    verified_urls = config.get('verified_urls', {})
    compound_url = verified_urls.get('compound')
    
    data = None
    source = "unknown"

    if compound_url:
        try:
            logger.info(f"Attempting to fetch compound data from verified URL: {compound_url}")
            content = fetch_url_content(compound_url)
            
            if isinstance(content, str):
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {"raw_content": content, "format": "text"}
            else:
                data = content
            
            source = "Real Data (Verified URL)"
            logger.info("Successfully fetched real compound data.")
            
        except Exception as e:
            logger.warning(f"Failed to fetch real compound data: {e}. Falling back to mock data.")
            source = "Mock Data (Fallback)"
            data = generate_mock_compound_data()
    else:
        logger.info("No verified compound URL configured. Generating mock data.")
        source = "Mock Data (No Config)"
        data = generate_mock_compound_data()

    # Save data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Compound data saved to {output_path} (Source: {source})")
    
    # Post-check: Verify disk usage
    try:
        check_disk_space(ESTIMATED_SIZE_MB * 1024 * 1024)
        logger.info("Disk space check passed after compound data ingestion.")
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

    return output_path

def save_data(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save data dictionary to a JSON file.

    Args:
        data: The data to save.
        output_path: The path to save the file to.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Data saved to {output_path}")

def run_all_ingestion() -> Dict[str, Path]:
    """
    Run all ingestion pipelines and return paths to generated files.

    Returns:
        Dictionary mapping data type to output file path.
    """
    logger.info("Starting full ingestion pipeline.")
    paths = {}
    
    try:
        paths['genomic'] = fetch_genomic_data()
    except Exception as e:
        logger.error(f"Genomic ingestion failed: {e}")
        # Continue with other data types if possible
    
    try:
        paths['env'] = fetch_env_data()
    except Exception as e:
        logger.error(f"Environmental ingestion failed: {e}")
    
    try:
        paths['compound'] = fetch_compound_data()
    except Exception as e:
        logger.error(f"Compound ingestion failed: {e}")
    
    logger.info("Ingestion pipeline completed.")
    return paths

def main():
    """
    Entry point for running the ingestion module directly.
    """
    configure_root_logger = None
    try:
        from utils.logging import configure_root_logger
    except ImportError:
        pass
    
    if configure_root_logger:
        configure_root_logger()
        
    logger.info("Running ingestion module via main()")
    try:
        paths = run_all_ingestion()
        print(f"Ingestion completed. Output files: {paths}")
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())