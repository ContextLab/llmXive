"""
Verified Accuracy Gate Implementation (Task T004)

Implements the 'Reference-Validator Agent' logic to verify external citations 
and data sources before processing.

This script checks the integrity and reachability of all dataset URLs against 
primary sources:
1. eBird source (HuggingFace 'vvud/eb-data')
2. NOAA/PRISM source (HuggingFace 'daymet/annual')

Output: data/provenance/accuracy_verification.json
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROVENANCE_DIR = PROJECT_ROOT / "data" / "provenance"
OUTPUT_FILE = PROVENANCE_DIR / "accuracy_verification.json"

# Verified Data Sources (from plan/spec)
DATA_SOURCES = [
    {
        "name": "eBird Sample Data",
        "source_id": "vvud/eb-data",
        "type": "huggingface",
        "description": "Verified sample eBird dataset for North America"
    },
    {
        "name": "NOAA/PRISM Climate Data",
        "source_id": "daymet/annual",
        "type": "huggingface",
        "description": "Annual climate data from NOAA/PRISM"
    }
]

def verify_huggingface_dataset(source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a HuggingFace dataset exists and is accessible.
    
    Args:
        source_config: Configuration dict with 'source_id' and other metadata
        
    Returns:
        Verification result dict with status, checksum (if available), and details
    """
    source_id = source_config["source_id"]
    result = {
        "source": source_id,
        "status": "unknown",
        "checksum": None,
        "details": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        logger.info(f"Verifying HuggingFace dataset: {source_id}")
        
        # Attempt to load dataset info with streaming to avoid full download
        dataset = load_dataset(source_id, streaming=True, trust_remote_code=True)
        
        # Verify we can access the data structure
        # Try to get the first example to confirm accessibility
        try:
            first_example = next(iter(dataset))
            result["status"] = "verified"
            result["details"]["accessible"] = True
            result["details"]["first_example_keys"] = list(first_example.keys())
            
            # Note: We don't compute a checksum here as streaming doesn't provide
            # a single file checksum. The dataset ID itself acts as the version identifier.
            result["details"]["version"] = source_id
            
            logger.info(f"Successfully verified dataset: {source_id}")
            
        except Exception as e:
            result["status"] = "failed"
            result["details"]["error"] = str(e)
            logger.error(f"Failed to access dataset {source_id}: {e}")
            
    except Exception as e:
        result["status"] = "failed"
        result["details"]["error"] = str(e)
        logger.error(f"Failed to verify dataset {source_id}: {e}")
        
    return result

def verify_accuracy_gate() -> Dict[str, Any]:
    """
    Main verification function that checks all configured data sources.
    
    Returns:
        Dictionary containing verification results for all sources
    """
    logger.info("Starting Verified Accuracy Gate verification...")
    
    verification_results = {
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "sources_checked": len(DATA_SOURCES),
        "all_verified": True,
        "results": []
    }
    
    failed_sources = []
    
    for source_config in DATA_SOURCES:
        logger.info(f"Checking source: {source_config['name']}")
        result = verify_huggingface_dataset(source_config)
        verification_results["results"].append(result)
        
        if result["status"] != "verified":
            verification_results["all_verified"] = False
            failed_sources.append(source_config["name"])
    
    # Log summary
    if verification_results["all_verified"]:
        logger.info("✓ All data sources verified successfully.")
    else:
        logger.error(f"✗ Verification failed for sources: {', '.join(failed_sources)}")
        
    return verification_results

def write_verification_report(results: Dict[str, Any]) -> None:
    """
    Write verification results to the provenance directory.
    
    Args:
        results: Verification results dictionary
    """
    # Ensure provenance directory exists
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Verification report written to: {OUTPUT_FILE}")

def main():
    """Main entry point for the accuracy gate verification."""
    try:
        # Run verification
        results = verify_accuracy_gate()
        
        # Write report
        write_verification_report(results)
        
        # Fail loudly if any source is not verified
        if not results["all_verified"]:
            failed_sources = [
                r["source"] for r in results["results"] 
                if r["status"] != "verified"
            ]
            raise RuntimeError(
                f"Accuracy Gate Verification Failed: "
                f"Sources not verified: {', '.join(failed_sources)}. "
                f"Cannot proceed with data processing."
            )
        
        logger.info("✓ Verified Accuracy Gate completed successfully.")
        return 0
        
    except RuntimeError as e:
        logger.error(f"Accuracy Gate Verification Failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
