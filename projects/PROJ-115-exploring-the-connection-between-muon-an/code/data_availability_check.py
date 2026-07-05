import json
import os
import sys
import urllib.request
import ssl
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/data_availability.log')
    ]
)
logger = logging.getLogger(__name__)

# Define data sources based on standard physics repositories and publications
DATA_SOURCES = {
    "Planck": {
        "type": "url",
        "url": "https://pla.esa.int/ftp/pla/full_release/Cosmological_Parameters.tar.gz",
        "description": "Planck 2018 Cosmological Parameters (Full Release)",
        "fallback_strategy": "Use Planck 2018 public CSV tables if tarball fails. If network fails, use hardcoded Planck 2018 central values for Omega_c h^2 and Omega_b h^2 from arXiv:1807.06209 as a temporary fallback for code structure testing (NOT for production physics).",
        "required": True
    },
    "Xenon1T": {
        "type": "url",
        "url": "https://xenon1t.web.cern.ch/Public/DarkMatter/ExclusionLimit.html",
        "description": "Xenon1T Dark Matter Exclusion Limit (HTML/Table)",
        "fallback_strategy": "Parse HTML table for limit points. If network fails or HTML structure changes, fallback to hardcoded array of (mass, cross_section) points extracted from the Xenon1T 2018 paper (Phys. Rev. D 98, 112009) which are standard reference values.",
        "required": True
    },
    "LEP": {
        "type": "url",
        "url": "https://pdg.lbl.gov/2024/reviews/rpp2024-rev-std-model.pdf",
        "description": "PDG Review of LEP Limits (PDF/Source)",
        "fallback_strategy": "Fetch PDG review. If network fails, fallback to hardcoded LEP limits for vector mediators from Ref [2014] (e.g., m_V > 10 GeV for g=0.1) as a placeholder for the scan logic, noting that this is a fallback.",
        "required": True
    }
}

def check_url_availability(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Check if a URL is reachable.
    Returns (is_available, message).
    """
    try:
        # Create an SSL context that does not verify certificates (for robustness in restricted envs)
        # In a production environment, this should be set to True and handled properly.
        context = ssl._create_unverified_context()
        logger.info(f"Checking URL: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=context, timeout=timeout) as response:
            if response.status == 200:
                logger.info(f"SUCCESS: {url} is accessible.")
                return True, "Accessible"
            else:
                logger.warning(f"FAILURE: {url} returned status {response.status}")
                return False, f"HTTP {response.status}"
    except urllib.error.URLError as e:
        logger.error(f"FAILURE: {url} - {e.reason}")
        return False, str(e.reason)
    except Exception as e:
        logger.error(f"FAILURE: {url} - Unexpected error: {e}")
        return False, str(e)

def check_local_file(filepath: str) -> Tuple[bool, str]:
    """
    Check if a local file exists.
    Returns (exists, message).
    """
    path = Path(filepath)
    if path.exists():
        logger.info(f"SUCCESS: Local file {filepath} exists.")
        return True, "File exists"
    else:
        logger.warning(f"FAILURE: Local file {filepath} not found.")
        return False, "File not found"

def run_checks(output_dir: str = "data") -> Dict:
    """
    Run availability checks for all defined data sources.
    Returns a dictionary of results.
    """
    results = {
        "timestamp": "2023-10-27T12:00:00Z", # Placeholder, actual time handled by logging
        "sources": {},
        "summary": {
            "total": len(DATA_SOURCES),
            "available": 0,
            "unavailable": 0
        }
    }

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for name, config in DATA_SOURCES.items():
        logger.info(f"Checking source: {name}")
        is_available = False
        message = ""
        
        if config["type"] == "url":
            is_available, message = check_url_availability(config["url"])
        elif config["type"] == "local":
            is_available, message = check_local_file(config["path"])
        
        results["sources"][name] = {
            "available": is_available,
            "message": message,
            "description": config["description"],
            "fallback_strategy": config["fallback_strategy"],
            "url": config.get("url", "N/A")
        }
        
        if is_available:
            results["summary"]["available"] += 1
        else:
            results["summary"]["unavailable"] += 1

    return results

def main():
    """
    Main entry point for the data availability check.
    Outputs a JSON report to data/data_availability_report.json.
    """
    logger.info("Starting Data Availability Check for Planck, Xenon1T, and LEP.")
    
    results = run_checks(output_dir="data")
    
    output_path = Path("data/data_availability_report.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Report saved to {output_path}")
    
    # Print summary to stdout
    print("\n--- Data Availability Summary ---")
    print(f"Total Sources: {results['summary']['total']}")
    print(f"Available: {results['summary']['available']}")
    print(f"Unavailable: {results['summary']['unavailable']}")
    print("Fallback strategies are documented in the JSON report.")
    print("---------------------------------\n")
    
    return results

if __name__ == "__main__":
    main()
