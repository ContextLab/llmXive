import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

def sanitize_url(url: str) -> str:
    """Sanitize URL to prevent injection attacks."""
    # Basic sanitization: ensure it starts with http
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL scheme: {url}")
    return url

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    safe_name = os.path.basename(filename)
    if not safe_name:
        raise ValueError("Empty filename")
    return safe_name

def write_verification_log(log_path: Path, status: str, message: str):
    """Write verification log to JSON."""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "message": message
    }
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def attempt_nist_fetch(url: str, output_dir: Path) -> bool:
    """Attempt to fetch data from NIST or specified URL."""
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        filename = sanitize_filename(url.split('/')[-1] or "adsorption_data.csv")
        output_path = output_dir / filename
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Successfully fetched data from {url} to {output_path}")
        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to fetch from NIST: {e}")
        return False

def attempt_fallback_fetch(url: str, output_dir: Path) -> bool:
    """Attempt fallback fetch from alternative source."""
    # Placeholder for fallback logic if needed
    return False

def main():
    """Main entry point for download script."""
    import argparse
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="Download adsorption data")
    parser.add_argument("--url", type=str, default="https://example.com/adsorption_data.csv")
    parser.add_argument("--output-dir", type=str, default="data/raw")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = output_dir / "verification_log.json"
    
    if attempt_nist_fetch(args.url, output_dir):
        write_verification_log(log_path, "SUCCESS", "Data fetched successfully from NIST.")
    else:
        write_verification_log(log_path, "FAILED", "Data fetch failed from all sources.")
        # T043a requirement: Fail loudly, no synthetic fallback
        raise RuntimeError("Data fetch failed. No synthetic data allowed.")

if __name__ == "__main__":
    main()
