import os
import hashlib
import logging
import yaml
from pathlib import Path
from datetime import datetime

def setup_save_logger(name: str = "save_cifs") -> logging.Logger:
    """Setup a dedicated logger for save operations."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_metadata(metadata_path: str) -> dict:
    """Load existing metadata.yaml if it exists."""
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_metadata(metadata: dict, metadata_path: str) -> None:
    """Save metadata to yaml file."""
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

def save_cifs_and_compute_checksums(
    cif_dir: str,
    metadata_path: str,
    logger: logging.Logger
) -> dict:
    """
    Save CIF files to the raw directory and compute their checksums.
    
    This function assumes CIF files are already present in cif_dir (downloaded by T007/T008).
    It computes checksums for all CIF files and updates the metadata.yaml.
    
    Args:
        cif_dir: Directory containing CIF files
        metadata_path: Path to metadata.yaml
        logger: Logger instance
    
    Returns:
        Dictionary of filenames to checksums
    """
    cif_dir_path = Path(cif_dir)
    if not cif_dir_path.exists():
        logger.error(f"CIF directory does not exist: {cif_dir}")
        return {}
    
    cif_files = list(cif_dir_path.glob("*.cif"))
    logger.info(f"Found {len(cif_files)} CIF files in {cif_dir}")
    
    checksums = {}
    material_ids = []
    
    for cif_file in cif_files:
        checksum = compute_sha256(str(cif_file))
        checksums[cif_file.name] = checksum
        # Extract material ID from filename (assuming format: {material_id}.cif)
        material_id = cif_file.stem
        material_ids.append(material_id)
        logger.debug(f"Computed checksum for {cif_file.name}: {checksum[:16]}...")
    
    # Update metadata.yaml
    existing_metadata = load_existing_metadata(metadata_path)
    
    # Initialize or update snapshot
    if "snapshots" not in existing_metadata:
        existing_metadata["snapshots"] = []
    
    snapshot = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": "cif_download",
        "material_ids": material_ids,
        "file_checksums": checksums,
        "directory": str(cif_dir_path)
    }
    existing_metadata["snapshots"].append(snapshot)
    
    save_metadata(existing_metadata, metadata_path)
    logger.info(f"Updated metadata at {metadata_path} with {len(material_ids)} materials")
    
    return checksums

def main():
    """Main entry point for saving CIFs and computing checksums."""
    logger = setup_save_logger()
    logger.info("Starting CIF checksum computation...")
    
    cif_dir = "data/raw/cif"
    metadata_path = "data/metadata.yaml"
    
    try:
        checksums = save_cifs_and_compute_checksums(
            cif_dir=cif_dir,
            metadata_path=metadata_path,
            logger=logger
        )
        logger.info(f"Checksum computation completed. Processed {len(checksums)} files.")
    except Exception as e:
        logger.error(f"Error during checksum computation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
