import os
import requests
from pathlib import Path
from typing import List

# The canonical COD bulk download URL as per spec
COD_BULK_URL = "https://www.crystallography.net/cod/cif.zip"
COD_SAMPLE_URL = "https://www.crystallography.net/cod/sample_ids.txt"

def fetch_cod_sample_ids(output_dir: str = "data/raw") -> List[str]:
    """
    Fetches a list of COD entry IDs from the canonical sample URL.
    Returns a list of IDs and writes them to a local file.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = Path(output_dir) / "cod_sample_ids.txt"

    try:
        response = requests.get(COD_SAMPLE_URL, timeout=30)
        response.raise_for_status()
        
        content = response.text
        ids = [line.strip() for line in content.splitlines() if line.strip()]
        
        with open(output_path, 'w') as f:
            f.write("\n".join(ids))
        
        return ids
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch COD sample IDs: {e}")

def download_cif(cif_id: str, output_dir: str = "data/raw") -> str:
    """
    Downloads a single CIF file for a given COD ID.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = Path(output_dir) / f"{cif_id}.cif"
    
    # Construct URL for specific CIF
    # COD structure is typically: https://www.crystallography.net/cod/{id}.cif
    url = f"https://www.crystallography.net/cod/{cif_id}.cif"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'w') as f:
            f.write(response.text)
        
        return str(output_path)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download CIF {cif_id}: {e}")
