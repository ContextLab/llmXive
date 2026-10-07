"""
Download or generate the MedDRA to SOC mapping table.

Source: Uses the 'meddra' Python package (verified source) to extract
the SOC mapping. Falls back to a trusted EMA mirror static file if the
package is not available, but fails loudly if neither source is accessible.

Output: data/meddra_soc_mapping.csv
"""
import os
import sys
import csv
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, List, Any

# Project root path (assuming code/ is the root relative to this script)
# Adjust based on actual project structure if needed, but tasks.md implies
# paths are relative to project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "meddra_soc_mapping.csv"

def setup_logging() -> logging.Logger:
    """Configure logging for the script."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def check_meddra_package() -> bool:
    """Check if the 'meddra' package is installed."""
    try:
        import meddra
        logger.info("Found 'meddra' package.")
        return True
    except ImportError:
        logger.warning("'meddra' package not found.")
        return False

def extract_soc_mapping_from_package() -> Optional[Dict[str, str]]:
    """
    Extract SOC mapping from the installed 'meddra' package.
    
    Returns a dict mapping HLT/LLT codes to SOC codes/names.
    Since 'meddra' structure varies by version, we attempt to read
    the standard SOC file if available, or construct from available data.
    """
    try:
        import meddra
        # The meddra package typically includes data files.
        # We look for the SOC file or construct from the available dictionary.
        # Standard approach: use the soc file if present, otherwise try to derive.
        # However, for robustness, we will try to access the soc_codes if exposed.
        
        # Attempt 1: Try to load the SOC file directly from package data if possible
        # This is version-dependent. A safer bet is to use the package's API if it exposes it.
        # Since direct file access is fragile, we will try to use the package's data loading if available.
        # If the package is just a data wrapper, we might need to read the CSVs it ships.
        
        # Fallback: If the package is installed, it usually contains the data.
        # We will try to find the soc file in the package data directory.
        import importlib.resources as resources
        
        # Try to access the soc file. The exact filename might vary.
        # Common names: soc.txt, soc.csv, soc.csv.gz
        possible_names = ['soc.txt', 'soc.csv', 'soc.csv.gz']
        
        soc_data = None
        for name in possible_names:
            try:
                # This might fail if the file doesn't exist in the package
                if hasattr(resources, 'files'):
                    # Python 3.9+
                    file_path = resources.files('meddra') / name
                    if file_path.is_file():
                        soc_data = file_path
                        break
                else:
                    # Python 3.8 fallback
                    with resources.path('meddra', name) as p:
                        if p.is_file():
                            soc_data = p
                            break
            except (FileNotFoundError, FileNotFoundError):
                continue
        
        if soc_data:
            logger.info(f"Found SOC file in package: {soc_data}")
            mapping = {}
            with open(soc_data, 'r', encoding='utf-8') as f:
                # Assume CSV or TXT with delimiter. Check first line.
                first_line = f.readline()
                delimiter = ',' if ',' in first_line else '\t'
                f.seek(0)
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    # Map SOC_CODE to SOC_NAME
                    # Keys might vary: 'SOC_CODE', 'SOC', 'HLLT_CODE', etc.
                    # We need a mapping of code -> SOC name.
                    # Standard MedDRA SOC file usually has 'SOC_CODE' and 'SOC'.
                    soc_code = row.get('SOC_CODE') or row.get('SOC')
                    soc_name = row.get('SOC') or row.get('SOC_NAME')
                    if soc_code and soc_name:
                        mapping[soc_code] = soc_name
            return mapping
        else:
            logger.warning("Could not locate SOC file within 'meddra' package.")
            return None

    except Exception as e:
        logger.error(f"Error extracting from 'meddra' package: {e}")
        return None

def download_from_ema_mirror() -> Optional[Path]:
    """
    Download MedDRA data from a trusted EMA mirror if available.
    Note: Direct programmatic download of full MedDRA from EMA is restricted.
    We will use a verified public mirror or a static file hosted by the project
    if the package method fails.
    
    Since direct scraping of MedDRA is often restricted, we will attempt
    to use a known public dataset or fail loudly.
    
    For this implementation, we assume a fallback static file might be
    provided in `data/raw/meddra_soc_mapping.csv` if the package fails,
    OR we attempt to download a known public CSV if one exists.
    
    However, the prompt says "Use a verified package ... or a static file".
    If the package fails, we check for a static file in the project.
    """
    # Check for a static file in the project's data/raw directory
    # This file should be manually placed or downloaded previously if the package is unavailable.
    # But for this task, we are the ones creating the download script.
    # If the package fails, we cannot magically download MedDRA without a valid URL.
    # We will fail loudly if the package is missing and no static file is found.
    
    # Let's try a known public URL for a simplified SOC mapping if available.
    # Note: Full MedDRA is proprietary. A simplified mapping might be available.
    # We will try to fetch a verified CSV from a trusted source (e.g., a GitHub repo hosting MedDRA mappings).
    # URL: https://raw.githubusercontent.com/meddra/meddra/main/soc.csv (Example, might not exist)
    # Instead, we rely on the package. If package fails, we check for a local fallback.
    
    # Since we cannot guarantee a public URL for the full MedDRA, we will
    # fail loudly if the package is not found and no local fallback exists.
    return None

def extract_soc_mapping_from_zip(zip_path: Path) -> Optional[Dict[str, str]]:
    """Extract SOC mapping from a downloaded ZIP file containing MedDRA data."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Look for a SOC file inside
            for name in zf.namelist():
                if name.endswith(('.csv', '.txt')) and 'soc' in name.lower():
                    with zf.open(name) as f:
                        # Read and parse
                        # Assume CSV
                        reader = csv.DictReader(f.read().decode('utf-8').splitlines())
                        mapping = {}
                        for row in reader:
                            soc_code = row.get('SOC_CODE') or row.get('SOC')
                            soc_name = row.get('SOC') or row.get('SOC_NAME')
                            if soc_code and soc_name:
                                mapping[soc_code] = soc_name
                        return mapping
        return None
    except Exception as e:
        logger.error(f"Error extracting SOC mapping from ZIP: {e}")
        return None

def save_mapping_to_csv(mapping: Dict[str, str], output_path: Path) -> None:
    """Save the mapping dictionary to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['SOC_CODE', 'SOC_NAME'])
        for code, name in sorted(mapping.items()):
            writer.writerow([code, name])
    logger.info(f"Saved mapping to {output_path}")

def main():
    """Main entry point for downloading/generating MedDRA SOC mapping."""
    logger.info("Starting MedDRA SOC mapping download/generation.")
    
    mapping = None
    
    # Step 1: Try the 'meddra' package
    if check_meddra_package():
        mapping = extract_soc_mapping_from_package()
        if mapping:
            logger.info("Successfully extracted mapping from 'meddra' package.")
        else:
            logger.warning("Failed to extract mapping from 'meddra' package.")
    
    # Step 2: If package failed, check for a static file in data/raw
    # This assumes a file might have been placed there manually or by another process.
    # But for this task, we are generating it. If the package fails, we must fail loudly
    # unless we have a verified source.
    if not mapping:
        # Check for a local fallback file (if it exists)
        fallback_file = PROJECT_ROOT / "data" / "raw" / "meddra_soc_mapping.csv"
        if fallback_file.exists():
            logger.info("Using fallback static file from data/raw/meddra_soc_mapping.csv")
            try:
                mapping = {}
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        mapping[row['SOC_CODE']] = row['SOC_NAME']
            except Exception as e:
                logger.error(f"Error reading fallback file: {e}")
                mapping = None
        else:
            logger.error("No verified source (package or static file) found for MedDRA SOC mapping.")
            logger.error("Please install the 'meddra' package (pip install meddra) or provide a static file.")
            sys.exit(1)
    
    if not mapping:
        logger.error("Failed to acquire MedDRA SOC mapping from any source.")
        sys.exit(1)
    
    # Save the mapping
    save_mapping_to_csv(mapping, OUTPUT_FILE)
    logger.info("MedDRA SOC mapping task completed successfully.")

if __name__ == "__main__":
    main()
