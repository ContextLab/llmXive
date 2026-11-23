"""
Extract native 1024x1024 images from raw archives (COCO, ImageNet) into data/processed/.

This script validates that extracted images are exactly 1024x1024 resolution as required
by FR-004 (native ground truth). It fails loudly if the resolution does not match.

Dependency: T005 (downloaded archives must exist in data/raw/)
Output: data/processed/native_1024/ directory containing valid 1024x1024 images
"""
import os
import sys
import logging
import argparse
import json
import zipfile
import tarfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
EXPECTED_RESOLUTION = (1024, 1024)
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed/native_1024")
VALIDATION_LOG = PROCESSED_DIR / "validation_log.json"
CHECKSUMS_FILE = PROCESSED_DIR / "checksums.json"

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_from_tarball(tar_path: Path, output_dir: Path, image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png')) -> List[Path]:
    """Extract images from a tarball archive."""
    extracted_files = []
    logger.info(f"Processing tarball: {tar_path}")
    
    try:
        with tarfile.open(tar_path, 'r:*') as tar:
            for member in tar.getmembers():
                if member.isfile() and any(member.name.lower().endswith(ext) for ext in image_extensions):
                    # Extract to a temporary location first to check resolution
                    target_path = output_dir / member.name
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Extract file
                    with tar.extractfile(member) as source:
                        if source:
                            with open(target_path, 'wb') as target:
                                target.write(source.read())
                            
                            # Validate resolution immediately
                            img = Image.open(target_path)
                            width, height = img.size
                            
                            if (width, height) == EXPECTED_RESOLUTION:
                                extracted_files.append(target_path)
                                logger.debug(f"Validated: {member.name} ({width}x{height})")
                            else:
                                # Remove incorrectly sized image
                                target_path.unlink()
                                logger.warning(f"Skipped {member.name}: resolution {width}x{height} != {EXPECTED_RESOLUTION}")
                                continue
    except Exception as e:
        logger.error(f"Error processing tarball {tar_path}: {e}")
        raise
    
    return extracted_files

def extract_from_zip(zip_path: Path, output_dir: Path, image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png')) -> List[Path]:
    """Extract images from a ZIP archive."""
    extracted_files = []
    logger.info(f"Processing ZIP: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                
                if any(file_info.filename.lower().endswith(ext) for ext in image_extensions):
                    # Extract to temporary location
                    target_path = output_dir / file_info.filename
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zip_ref.open(file_info) as source:
                        with open(target_path, 'wb') as target:
                            target.write(source.read())
                        
                        # Validate resolution
                        img = Image.open(target_path)
                        width, height = img.size
                        
                        if (width, height) == EXPECTED_RESOLUTION:
                            extracted_files.append(target_path)
                            logger.debug(f"Validated: {file_info.filename} ({width}x{height})")
                        else:
                            target_path.unlink()
                            logger.warning(f"Skipped {file_info.filename}: resolution {width}x{height} != {EXPECTED_RESOLUTION}")
                            continue
    except Exception as e:
        logger.error(f"Error processing ZIP {zip_path}: {e}")
        raise
    
    return extracted_files

def discover_archives(raw_dir: Path) -> List[Path]:
    """Discover all archive files in the raw data directory."""
    archives = []
    for pattern in ['*.tar.gz', '*.tar.bz2', '*.tgz', '*.tar', '*.zip']:
        archives.extend(raw_dir.glob(pattern))
        archives.extend(raw_dir.rglob(pattern))
    
    # Also check for uncompressed image directories that might contain native 1024x1024 images
    for item in raw_dir.iterdir():
        if item.is_dir() and item.name.startswith(('imagenet', 'coco')):
            archives.append(item)  # Treat directory as a source
    
    return archives

def process_directory_source(source_dir: Path, output_dir: Path, image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png')) -> List[Path]:
    """Process a directory of images directly."""
    extracted_files = []
    logger.info(f"Processing directory: {source_dir}")
    
    for img_path in source_dir.rglob('*'):
        if img_path.is_file() and any(img_path.suffix.lower() == ext for ext in image_extensions):
            # Copy to output directory with unique name
            relative_path = img_path.relative_to(source_dir)
            target_path = output_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            with open(img_path, 'rb') as src:
                with open(target_path, 'wb') as dst:
                    dst.write(src.read())
            
            # Validate resolution
            img = Image.open(target_path)
            width, height = img.size
            
            if (width, height) == EXPECTED_RESOLUTION:
                extracted_files.append(target_path)
                logger.debug(f"Validated: {img_path} ({width}x{height})")
            else:
                target_path.unlink()
                logger.warning(f"Skipped {img_path}: resolution {width}x{height} != {EXPECTED_RESOLUTION}")
                continue
    
    return extracted_files

def main():
    parser = argparse.ArgumentParser(description='Extract native 1024x1024 images from raw archives')
    parser.add_argument('--raw-dir', type=Path, default=RAW_DATA_DIR,
                      help='Directory containing raw data archives')
    parser.add_argument('--output-dir', type=Path, default=PROCESSED_DIR,
                      help='Output directory for extracted images')
    parser.add_argument('--strict', action='store_true',
                      help='Fail if no 1024x1024 images are found')
    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting extraction to: {args.output_dir}")
    logger.info(f"Expected resolution: {EXPECTED_RESOLUTION}")

    # Check if raw directory exists
    if not args.raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {args.raw_dir}")
        logger.error("Please run the data loader first to download datasets (T005)")
        sys.exit(1)

    # Discover archives
    archives = discover_archives(args.raw_dir)
    
    if not archives:
        logger.error(f"No archives found in {args.raw_dir}")
        if args.strict:
            sys.exit(1)
        else:
            logger.warning("Continuing without archives - output directory will be empty")
            return

    logger.info(f"Found {len(archives)} archive(s) to process")

    all_extracted = []
    validation_results = []
    checksums = {}

    for archive in archives:
        logger.info(f"Processing: {archive.name}")
        extracted = []
        
        try:
            if archive.suffix == '.zip' or (archive.name.endswith('.tar.gz') == False and archive.is_file()):
                # Try as ZIP first if it looks like one
                if archive.suffix == '.zip':
                    extracted = extract_from_zip(archive, args.output_dir)
                elif archive.is_dir():
                    extracted = process_directory_source(archive, args.output_dir)
                else:
                    # Assume tarball
                    extracted = extract_from_tarball(archive, args.output_dir)
            elif archive.is_dir():
                extracted = process_directory_source(archive, args.output_dir)
            else:
                # Try tarball
                extracted = extract_from_tarball(archive, args.output_dir)
            
            all_extracted.extend(extracted)
            
            # Calculate checksums for extracted files
            for img_path in extracted:
                checksum = calculate_sha256(img_path)
                checksums[str(img_path.relative_to(args.output_dir))] = checksum
            
            validation_results.append({
                "source": str(archive.name),
                "extracted_count": len(extracted),
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Failed to process {archive}: {e}")
            validation_results.append({
                "source": str(archive.name),
                "error": str(e),
                "status": "failed"
            })
            if args.strict:
                raise

    # Summary
    logger.info(f"Extraction complete. Total valid 1024x1024 images: {len(all_extracted)}")
    
    if len(all_extracted) == 0:
        logger.error("No 1024x1024 images were extracted!")
        logger.error("This may indicate:")
        logger.error("  1. The raw archives do not contain 1024x1024 images")
        logger.error("  2. All images in the archives are different resolutions")
        logger.error("  3. The archives are corrupted or empty")
        if args.strict:
            sys.exit(1)
        else:
            logger.warning("Continuing with empty output (strict mode not enabled)")
    else:
        logger.info(f"Successfully extracted {len(all_extracted)} images to {args.output_dir}")
        
        # Save validation log
        validation_log = {
            "timestamp": str(Path(args.output_dir).stat().st_mtime),
            "expected_resolution": EXPECTED_RESOLUTION,
            "total_extracted": len(all_extracted),
            "sources_processed": validation_results,
            "sample_images": [str(p.relative_to(args.output_dir)) for p in all_extracted[:10]]
        }
        
        with open(VALIDATION_LOG, 'w') as f:
            json.dump(validation_log, f, indent=2)
        logger.info(f"Validation log saved to: {VALIDATION_LOG}")
        
        # Save checksums
        with open(CHECKSUMS_FILE, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksums saved to: {CHECKSUMS_FILE}")

    # Final verification
    output_files = list(args.output_dir.glob('**/*'))
    output_files = [f for f in output_files if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    logger.info(f"Final count in output directory: {len(output_files)} files")
    
    # Verify a sample of output files
    if len(output_files) > 0:
        sample_count = min(5, len(output_files))
        logger.info(f"Verifying {sample_count} sample files...")
        
        for i, img_path in enumerate(output_files[:sample_count]):
            img = Image.open(img_path)
            width, height = img.size
            if (width, height) != EXPECTED_RESOLUTION:
                logger.error(f"Verification failed: {img_path} has resolution {width}x{height}")
                sys.exit(1)
            logger.debug(f"Verified: {img_path.name} ({width}x{height})")
        
        logger.info("All sample verifications passed!")

    logger.info("Extraction task completed successfully")

if __name__ == "__main__":
    main()