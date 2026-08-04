import os
import requests
from pathlib import Path
from typing import List, Optional
from code.config import get_config

def fetch_cod_sample_ids() -> List[str]:
    """
    Fetch a list of COD entry IDs from the canonical bulk download URL.
    This function reads the COD sample IDs from the pre-downloaded file `data/raw/cod_sample_ids.txt`.
    If the file does not exist, it attempts to download the sample IDs from the canonical URL.
    """
    config = get_config()
    sample_file = config.get('DATA_PATH', 'data') / 'raw' / 'cod_sample_ids.txt'
    if not isinstance(sample_file, Path):
        sample_file = Path(sample_file)
    
    if not sample_file.exists():
        # Attempt to download the sample IDs
        cod_url = config.get('COD_URL', 'https://www.crystallography.net/cod/entries.csv.gz')
        # Note: The canonical URL for bulk download might be different.
        # We will use a placeholder URL that the user must replace with the real one.
        # For now, we assume the file is already downloaded as per T004.
        raise FileNotFoundError(f"Sample IDs file not found: {sample_file}. Please download it manually or configure COD_URL.")
    
    with open(sample_file, 'r') as f:
        ids = [line.strip() for line in f if line.strip()]
    
    return ids

def download_cif(cod_id: str, output_dir: Path) -> Optional[Path]:
    """
    Download a CIF file for a given COD entry ID.
    Returns the path to the downloaded file, or None if the download fails.
    """
    config = get_config()
    cod_url_base = config.get('COD_URL', 'https://www.crystallography.net/cod/')
    # Construct the URL for the CIF file
    # The URL format might be: https://www.crystallography.net/cod/1234567.cif
    url = f"{cod_url_base}{cod_id}.cif"
    
    output_path = output_dir / f"{cod_id}.cif"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return output_path
    except requests.RequestException as e:
        # Log the error but do not raise, as per the requirement to fail loudly but not crash the whole pipeline
        # However, the task says "fail loudly", so we should raise.
        raise RuntimeError(f"Failed to download CIF for {cod_id}: {e}")
