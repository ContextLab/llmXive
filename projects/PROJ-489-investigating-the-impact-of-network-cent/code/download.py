import json
import logging
import shutil
from pathlib import Path
from typing import Dict
import mne
import os
import hashlib
from integrity import calculate_file_checksum, verify_manifest, generate_manifest
from config_utils import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(path: str = "code/config.yaml") -> Dict:
    """Load configuration from YAML file."""
    import yaml
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {path} not found. Using defaults.")
        return {}

def main():
    """
    Main entry point for downloading Sleep-EDF dataset.
    Implements error handling for corrupted .edf files:
    - Logs error for each corrupted file
    - Skips the corrupted file
    - Continues processing remaining files
    """
    config = load_config()
    base_dir = Path(config.get("paths", {}).get("raw_data", "data/raw"))
    base_dir.mkdir(parents=True, exist_ok=True)

    # List of subject IDs to download (example subset for testing)
    # In production, this would come from config or a manifest
    subject_ids = ["ST50", "ST51", "ST52", "ST53", "ST54"]
    
    successful_downloads = []
    corrupted_files = []
    skipped_files = []

    logger.info(f"Starting download process for {len(subject_ids)} subjects...")
    logger.info(f"Target directory: {base_dir}")

    for subject_id in subject_ids:
        try:
            # Construct the dataset name
            dataset_name = f"SleepEDF_small-EDF-F-{subject_id}-PSG.edf"
            local_path = base_dir / dataset_name
            
            if local_path.exists():
                logger.info(f"Skipping {subject_id}: File already exists.")
                successful_downloads.append(subject_id)
                continue

            logger.info(f"Downloading {subject_id}...")
            
            # Attempt to download using MNE
            # Using mne.datasets.sleep_edf.fetch_sleep_edf_small as it's the standard way
            # to get the small subset for testing
            try:
                # MNE's fetch functions return the path to the downloaded file
                # We'll simulate the download by trying to load a known file
                # In a real scenario, this would be: mne.datasets.sleep_edf.fetch_sleep_edf_small(...)
                # For this implementation, we'll attempt to fetch the specific file
                
                # Since we can't easily fetch a single file, we'll fetch the whole small dataset
                # and then copy the specific file we need
                data_path = mne.datasets.sleep_edf.data_path(download=False)
                
                if data_path is None or not Path(data_path).exists():
                    logger.info(f"Dataset not found locally. Attempting download for {subject_id}...")
                    data_path = mne.datasets.sleep_edf.data_path(download=True)
                
                source_file = Path(data_path) / dataset_name
                
                if not source_file.exists():
                    # Try alternative naming convention
                    alt_name = f"SleepEDF_small-EDF-F-{subject_id}-PSG.edf"
                    source_file = Path(data_path) / alt_name
                    
                    if not source_file.exists():
                        logger.error(f"File {dataset_name} not found in Sleep-EDF dataset.")
                        corrupted_files.append((subject_id, "File not found in dataset"))
                        skipped_files.append(subject_id)
                        continue
                
                # Copy file to our raw data directory
                shutil.copy2(source_file, local_path)
                
                # Verify checksum if manifest exists
                manifest_path = base_dir.parent / "manifest.json"
                if manifest_path.exists():
                    if not verify_manifest(local_path, manifest_path):
                        logger.warning(f"Checksum verification failed for {local_path}. File may be corrupted.")
                        # Attempt to re-download or skip
                        os.remove(local_path)
                        corrupted_files.append((subject_id, "Checksum verification failed"))
                        skipped_files.append(subject_id)
                        continue
                
                logger.info(f"Successfully downloaded {subject_id}")
                successful_downloads.append(subject_id)
                
            except Exception as e:
                logger.error(f"Error downloading {subject_id}: {str(e)}")
                corrupted_files.append((subject_id, str(e)))
                skipped_files.append(subject_id)
                continue

        except Exception as e:
            logger.error(f"Unexpected error processing {subject_id}: {str(e)}")
            corrupted_files.append((subject_id, f"Unexpected error: {str(e)}"))
            skipped_files.append(subject_id)
            continue

    # Summary
    logger.info("=" * 50)
    logger.info("Download Summary:")
    logger.info(f"  Total subjects attempted: {len(subject_ids)}")
    logger.info(f"  Successful downloads: {len(successful_downloads)}")
    logger.info(f"  Skipped (already exists or error): {len(skipped_files)}")
    logger.info(f"  Corrupted files detected: {len(corrupted_files)}")
    
    if corrupted_files:
        logger.warning("Corrupted files detected:")
        for subj, reason in corrupted_files:
            logger.warning(f"  - {subj}: {reason}")
    
    if successful_downloads:
        logger.info("Successfully downloaded subjects:")
        for subj in successful_downloads:
            logger.info(f"  - {subj}")
    
    # Save results
    results = {
        "successful_downloads": successful_downloads,
        "skipped_files": skipped_files,
        "corrupted_files": [dict(zip(["subject_id", "reason"], item)) for item in corrupted_files],
        "total_attempted": len(subject_ids),
        "success_count": len(successful_downloads),
        "corruption_count": len(corrupted_files)
    }
    
    results_path = base_dir.parent / "download_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    
    # Generate manifest for downloaded files
    if successful_downloads:
        generate_manifest(base_dir)
        logger.info(f"Manifest generated at {base_dir.parent / 'manifest.json'}")

    return results

if __name__ == "__main__":
    main()