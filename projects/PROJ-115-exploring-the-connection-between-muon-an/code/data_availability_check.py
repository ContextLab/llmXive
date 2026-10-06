import json
import os
import sys
import urllib.request
import ssl
from pathlib import Path
from typing import Dict, List, Any, Optional
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

# Define verified data sources based on project requirements and standard physics repositories
# Planck: ESA Planck Legacy Archive (publicly accessible)
# Xenon1T: Published exclusion limits (hardcoded fallback as per FR-003, but we verify the source)
# LEP: CERN Data Center / PDG summaries
DATA_SOURCES = {
    "planck_relic_density": {
        "name": "Planck 2018 Relic Density Constraints",
        "type": "url",
        "url": "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CompMap_2018_R2.01.fits",
        "description": "Planck 2018 CMB power spectra and derived parameters (Omega_m h^2)",
        "fallback_strategy": "Use hardcoded Planck 2018 central values (Omega_m h^2 = 0.1430 +/- 0.0011) from physics.fallback_data",
        "required_for": ["US4", "US1"],
        "status": "PENDING"
    },
    "xenon1t_limits": {
        "name": "Xenon1T Spin-Independent Cross-Section Limits",
        "type": "url",
        "url": "https://xenon1t.lbl.gov/data/2018/2018-12-19_XENON1T_Results.pdf",
        "description": "Xenon1T 2018 exclusion curve data (m_DM vs sigma_SI)",
        "fallback_strategy": "Use hardcoded curve points from physics.fallback_data.get_xenon1t_limits() as per FR-003",
        "required_for": ["US1", "US4"],
        "status": "PENDING"
    },
    "lep_exclusion": {
        "name": "LEP Chargino/Neutralino Limits",
        "type": "url",
        "url": "https://pdg.lbl.gov/2024/reviews/rpp2024-rev-lepton-flavor-universality.pdf", 
        "description": "PDG summary of LEP limits used as proxy for direct LEP data (Ref [2014] in spec)",
        "fallback_strategy": "Parse PDG tables or use hardcoded LEP limits from physics.fallback_data.get_lep_limits()",
        "required_for": ["US1"],
        "status": "PENDING"
    }
}

def check_url_availability(url: str, timeout: int = 10) -> bool:
    """Check if a URL is accessible."""
    try:
        # Create an SSL context that doesn't verify certificates for public data access
        # In production, this should be handled properly, but for availability check we allow it
        context = ssl._create_unverified_context()
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, context=context, timeout=timeout) as response:
            return response.status == 200
    except Exception as e:
        logger.warning(f"URL check failed for {url}: {e}")
        return False

def check_local_file(file_path: str) -> bool:
    """Check if a local file exists."""
    path = Path(file_path)
    return path.exists() and path.stat().st_size > 0

def run_checks() -> Dict[str, Any]:
    """Run availability checks for all defined data sources."""
    results = {}
    all_available = True

    for key, source in DATA_SOURCES.items():
        logger.info(f"Checking availability for: {source['name']}")
        
        if source['type'] == 'url':
            available = check_url_availability(source['url'])
            logger.info(f"  URL Status: {'Available' if available else 'Unavailable'}")
        elif source['type'] == 'local':
            available = check_local_file(source['path'])
            logger.info(f"  Local File Status: {'Available' if available else 'Unavailable'}")
        else:
            logger.error(f"Unknown source type: {source['type']}")
            available = False

        results[key] = {
            "name": source['name'],
            "available": available,
            "type": source['type'],
            "url": source.get('url', 'N/A'),
            "fallback_strategy": source['fallback_strategy'],
            "required_for": source['required_for']
        }

        if not available:
            all_available = False
            logger.warning(f"  -> FALLBACK REQUIRED: {source['fallback_strategy']}")

    return {
        "summary": {
            "total_sources": len(DATA_SOURCES),
            "available_sources": sum(1 for r in results.values() if r['available']),
            "all_available": all_available,
            "fallbacks_defined": all(r['fallback_strategy'] for r in results.values())
        },
        "detailed_results": results
    }

def main():
    """Main entry point for data availability check."""
    logger.info("Starting Data Availability Check for PROJ-115")
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Run checks
    results = run_checks()
    
    # Save results to JSON
    output_path = data_dir / "data_availability_report.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Report saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("DATA AVAILABILITY SUMMARY")
    print("="*60)
    print(f"Total Sources: {results['summary']['total_sources']}")
    print(f"Available: {results['summary']['available_sources']}")
    print(f"All Available: {results['summary']['all_available']}")
    print(f"Fallbacks Defined: {results['summary']['fallbacks_defined']}")
    print("="*60)
    
    for key, res in results['detailed_results'].items():
        status = "✓ AVAILABLE" if res['available'] else "✗ UNAVAILABLE"
        print(f"{res['name']}: {status}")
        if not res['available']:
            print(f"  Fallback: {res['fallback_strategy']}")
    print("="*60)
    
    # Return exit code based on availability (but we always have fallbacks)
    return 0

if __name__ == "__main__":
    sys.exit(main())
