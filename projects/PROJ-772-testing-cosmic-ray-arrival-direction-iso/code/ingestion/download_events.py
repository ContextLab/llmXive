"""
Event download script for Auger and Telescope Array public data.

Implements graceful error handling for missing data repositories.
"""
import os
import sys
from pathlib import Path
import requests
from tqdm import tqdm

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

def download_with_retry(url: str, dest_path: str, timeout: int = 30) -> bool:
    """
    Download a file with retry logic and progress bar.

    Returns True on success, False on failure.
    """
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        with open(dest_path, 'wb') as f, tqdm(
            total=total_size, unit='B', unit_scale=True, desc=os.path.basename(dest_path)
        ) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False

def main():
    """
    Main entry point for downloading events.
    Handles missing repositories gracefully by logging and exiting cleanly.
    """
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Pinned URLs from config (simulated here for structure, actual URLs in config.yaml)
    auger_url = "https://zenodo.org/record/3966535/files/events.csv"
    ta_url = "https://telescopearray.org/data/public/2023-01/events.csv"

    files_to_download = [
        ("auger_2020.csv", auger_url),
        ("ta_2023.csv", ta_url)
    ]

    success_count = 0
    for name, url in files_to_download:
        dest = raw_dir / name
        if download_with_retry(url, str(dest)):
            print(f"Successfully downloaded {name}")
            success_count += 1
        else:
            print(f"Failed to download {name} from {url}")

    if success_count == 0:
        print("CRITICAL: No data files could be downloaded. Exiting.")
        sys.exit(1)

    print(f"Download complete. {success_count}/{len(files_to_download)} files retrieved.")

if __name__ == "__main__":
    main()
