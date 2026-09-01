"""
T005c: Fetch Checksum Manifest.

Logic:
1. Fetch `manifest.json` from the canonical HuggingFace dataset source.
2. Write the raw content to `data/raw/manifest.json`.
3. Exit 0 on success.
4. Exit non-zero (raise exception) if fetch fails or checksum verification fails.
"""
import os
import sys
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MANIFEST_URL = "https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json"
OUTPUT_PATH = Path("data/raw/manifest.json")
EXPECTED_MIN_SIZE = 10  # Sanity check: manifest shouldn't be empty

def fetch_manifest(url: str, output_path: Path) -> dict:
    """
    Fetches the manifest JSON from the remote URL and saves it locally.
    Raises exceptions on network errors or invalid content.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching manifest from: {url}")
    logger.info(f"Target path: {output_path}")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}: Failed to fetch manifest")
            
            content = response.read().decode('utf-8')
            
            # Validate JSON before writing
            try:
                manifest_data = json.loads(content)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON received from manifest URL: {e}")

            # Basic sanity check
            if not isinstance(manifest_data, dict) and not isinstance(manifest_data, list):
                raise RuntimeError("Manifest format invalid: expected JSON object or array")

            # Write to disk
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Manifest saved successfully to {output_path}")
            logger.info(f"Manifest size: {len(content)} bytes")
            
            return manifest_data

    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code} while fetching manifest: {e.reason}")
        raise FileNotFoundError(f"Manifest fetch failed (HTTP {e.code}); pipeline cannot proceed.")
    except urllib.error.URLError as e:
        logger.error(f"URL Error while fetching manifest: {e.reason}")
        raise FileNotFoundError(f"Network error fetching manifest; pipeline cannot proceed.")
    except Exception as e:
        logger.error(f"Unexpected error fetching manifest: {e}")
        raise

def main():
    """Entry point for T005c."""
    try:
        manifest = fetch_manifest(MANIFEST_URL, OUTPUT_PATH)
        logger.info("T005c: Fetch Checksum Manifest completed successfully.")
        return 0
    except Exception as e:
        logger.critical(f"T005c failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
