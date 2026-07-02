"""
T004: Verify dataset availability for Planck, Xenon1T, and LEP; document fallback strategies.

This script attempts to fetch or verify the existence of real data sources required for the
muon g-2 dark matter analysis. It checks:
1. Planck 2018 Relic Density: Available via standard cosmological constants (no external fetch needed).
2. Xenon1T Limits: Attempts to fetch from the public Zenodo repository.
3. LEP Limits: Attempts to fetch from the CERN Data Preservation portal or a known mirror.

If a source is unreachable, it logs the fallback strategy defined in the project plan.
Outputs a summary report to `data/data_availability_report.json`.
"""
import json
import os
import sys
import urllib.request
import ssl
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

# Output paths relative to project root
OUTPUT_DIR = Path("data")
REPORT_PATH = OUTPUT_DIR / "data_availability_report.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Data Source Definitions ---

SOURCES = {
    "Planck_2018": {
        "name": "Planck 2018 Relic Density Constraints",
        "type": "constant",
        "url": None,
        "description": "Standard cosmological constants (Omega_c h^2). No external fetch required.",
        "fallback": "Use hardcoded Planck 2018 central value: 0.120 +/- 0.001."
    },
    "Xenon1T_2018": {
        "name": "Xenon1T Spin-Independent Limits (2018)",
        "type": "url",
        # Zenodo record for XENON1T 1T run results
        "url": "https://zenodo.org/api/records/3364945/files-archive",
        "local_check": "data/xenon1t_limits.parquet",
        "description": "Spin-independent cross-section limits vs DM mass.",
        "fallback": "Use hardcoded piecewise polynomial approximation of the 2018 curve if fetch fails."
    },
    "LEP_Monophoton": {
        "name": "LEP Monophoton Limits (2004-2014)",
        "type": "url",
        # Attempting a generic CERN data preservation link or a known mirror.
        # If this specific URL is not reachable, we fall back to parsing paper tables.
        "url": "https://cds.cern.ch/record/2004841/files/1408.2878.pdf", 
        "local_check": "data/lep_limits.parquet",
        "description": "LEP limits on contact interactions/monophoton events.",
        "fallback": "Parse numerical tables from the paper (arXiv:1408.2878) if direct data fetch fails."
    }
}

def check_url_availability(url: str, timeout: int = 10) -> bool:
    """Check if a URL is reachable."""
    if not url:
        return False
    try:
        # Create an SSL context that does not verify certificates (for some older repos)
        # In a production environment, proper cert verification is preferred.
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            return response.status == 200
    except Exception:
        return False

def check_local_file(path: str) -> bool:
    """Check if a local file exists."""
    return os.path.exists(path)

def run_checks() -> Dict[str, Any]:
    """Run availability checks for all defined sources."""
    results = {}
    timestamp = datetime.now().isoformat()

    for key, config in SOURCES.items():
        status = {
            "name": config["name"],
            "type": config["type"],
            "description": config["description"],
            "available": False,
            "method": None,
            "details": "",
            "fallback_strategy": config["fallback"]
        }

        if config["type"] == "constant":
            status["available"] = True
            status["method"] = "hardcoded_constant"
            status["details"] = "No external fetch required. Value defined in code."
        
        elif config["type"] == "url":
            # Check local first (if we assume previous runs might have downloaded it)
            if "local_check" in config:
                local_path = Path(config["local_check"])
                if local_path.exists():
                    status["available"] = True
                    status["method"] = "local_cache"
                    status["details"] = f"Found local file: {local_path}"
            
            # If not local, try to fetch
            if not status["available"]:
                if check_url_availability(config["url"]):
                    status["available"] = True
                    status["method"] = "remote_fetch"
                    status["details"] = f"URL reachable: {config['url']}"
                else:
                    status["available"] = False
                    status["method"] = "fetch_failed"
                    status["details"] = f"URL unreachable: {config['url']}"

        results[key] = status

    return {
        "timestamp": timestamp,
        "project": "PROJ-115-exploring-the-connection-between-muon-an",
        "task": "T004",
        "sources": results,
        "summary": {
            "total_sources": len(SOURCES),
            "available_count": sum(1 for s in results.values() if s["available"]),
            "fallbacks_required": sum(1 for s in results.values() if not s["available"])
        }
    }

def main():
    print("Starting T004: Data Availability Check...")
    report = run_checks()
    
    # Save report
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report generated: {REPORT_PATH}")
    
    # Print summary to stdout
    summary = report["summary"]
    print(f"Total sources: {summary['total_sources']}")
    print(f"Available: {summary['available_count']}")
    print(f"Requires fallback: {summary['fallbacks_required']}")
    
    for key, data in report["sources"].items():
        status_icon = "✓" if data["available"] else "✗"
        print(f"{status_icon} {data['name']}: {data['method']}")
        if not data["available"]:
            print(f"   -> Fallback: {data['fallback_strategy'][:60]}...")

    # Exit with 0 regardless of availability, as fallbacks are valid strategies
    return 0

if __name__ == "__main__":
    sys.exit(main())
