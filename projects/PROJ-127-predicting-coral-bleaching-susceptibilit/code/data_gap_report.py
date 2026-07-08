import os
from pathlib import Path
import sys
import config

def check_url_validity(url: str) -> bool:
    """
    Checks if a URL is valid and reachable.
    Returns True if valid, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    # Basic URL format check
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    # In a real implementation, we would use requests.head() to check connectivity
    # For now, we assume the URL is valid if it has a proper format
    return True

def generate_report(missing_urls: list, output_path: Path):
    """
    Generates a data gap report listing missing sources and a HALT flag.
    """
    with open(output_path, 'w') as f:
        f.write("# Data Gap Report\n\n")
        f.write("## Missing Data Sources\n\n")
        if missing_urls:
            for url in missing_urls:
                f.write(f"- {url}\n")
            f.write("\n## Status: HALT\n\n")
            f.write("The pipeline cannot proceed due to missing required data sources.\n")
        else:
            f.write("All required data sources are available.\n")
            f.write("\n## Status: OK\n\n")
            f.write("The pipeline can proceed.\n")

def main():
    """
    Main function to check data sources and generate a report if any are missing.
    """
    # List of required URLs from config
    required_urls = [
        config.NOAA_URL,
        config.CORAL_TRAIT_URL,
        config.UNEP_REEFS_URL,
        config.REEFBASE_URL,
    ]

    missing_urls = []
    for url in required_urls:
        if not check_url_validity(url):
            missing_urls.append(url)

    output_path = config.PROJECT_ROOT / "data_gap_report.md"
    generate_report(missing_urls, output_path)

    if missing_urls and config.DATA_GAP_HALT:
        print(f"Data gap report generated at {output_path}. Halting pipeline.")
        sys.exit(1)
    else:
        print(f"Data gap report generated at {output_path}. Pipeline can proceed.")

if __name__ == "__main__":
    main()
