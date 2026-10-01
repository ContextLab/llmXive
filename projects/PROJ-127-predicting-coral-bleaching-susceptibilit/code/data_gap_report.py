import os
import sys
import requests
from pathlib import Path
import config

def check_url_validity(url: str) -> bool:
    """
    Checks if a URL is valid and reachable.
    Returns True if valid and reachable (HTTP 200/302/301), False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL format check
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    
    try:
        # Use HEAD request to check reachability without downloading content
        # Timeout set to 10 seconds to prevent hanging
        response = requests.head(url, timeout=10, allow_redirects=True)
        # Consider 200, 301, 302 as valid (redirects are fine)
        return response.status_code in [200, 301, 302]
    except requests.exceptions.RequestException:
        # Connection error, timeout, SSL error, etc.
        return False

def generate_report(missing_urls: list, output_path: Path):
    """
    Generates a data gap report listing missing sources and a HALT flag.
    """
    with open(output_path, 'w') as f:
        f.write("# Data Gap Report\n\n")
        f.write("## Generated At: " + str(Path.cwd()) + "\n\n")
        f.write("## Missing Data Sources\n\n")
        
        if missing_urls:
            for url in missing_urls:
                f.write(f"- {url}\n")
            f.write("\n## Status: HALT\n\n")
            f.write("The pipeline cannot proceed due to missing required data sources.\n")
            f.write("Please verify the URLs in `code/config.py` and ensure network connectivity.\n")
        else:
            f.write("All required data sources are available and reachable.\n")
            f.write("\n## Status: OK\n\n")
            f.write("The pipeline can proceed to data ingestion.\n")

def main():
    """
    Main function to check data sources and generate a report if any are missing.
    """
    # List of required URLs from config
    required_urls = [
        ("NOAA", config.NOAA_URL),
        ("Coral Trait Database", config.CORAL_TRAIT_URL),
        ("UNEP Reefs", config.UNEP_REEFS_URL),
        ("ReefBase", config.REEFBASE_URL),
    ]

    missing_urls = []
    for name, url in required_urls:
        if not check_url_validity(url):
            missing_urls.append(f"{name}: {url}")

    output_path = config.PROJECT_ROOT / "data_gap_report.md"
    generate_report(missing_urls, output_path)

    if missing_urls and config.DATA_GAP_HALT:
        print(f"Data gap report generated at {output_path}. Halting pipeline.")
        print(f"Missing sources: {len(missing_urls)}")
        sys.exit(1)
    else:
        if missing_urls:
            print(f"Data gap report generated at {output_path}. Warning: {len(missing_urls)} sources missing, but HALT is disabled.")
        else:
            print(f"Data gap report generated at {output_path}. All sources available.")

if __name__ == "__main__":
    main()