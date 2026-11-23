"""
Lifecycle Manager for PROJ-002.

This script is designed to be triggered by a cron job. It manages the lifecycle
of FASTQ files based on a configurable retention period:
1. Identifies FASTQ files older than the retention period.
2. Compresses them (gzip).
3. Deploys the compressed archives to Zenodo (creates a new deposit).
4. Records the Zenodo DOI in metadata.json.
5. Deletes the local copies (both original and compressed).
"""
import os
import shutil
import json
import subprocess
import glob
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# Import local utilities
from code.utils.logger import setup_logger, log_pipeline_step
from code.utils.hash import calculate_sha256
from code.utils.env_config import load_environment_config

# Initialize logger
logger = setup_logger()

def compress_fastqs(fastq_files: list[Path], output_dir: Path) -> list[Path]:
    """
    Compresses a list of FASTQ files using gzip.
    
    Args:
        fastq_files: List of Path objects to original FASTQ files.
        output_dir: Directory where compressed files will be saved.
        
    Returns:
        List of Path objects to the compressed .gz files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    compressed_files = []
    
    logger.info(f"Compressing {len(fastq_files)} FASTQ files...")
    
    for file_path in fastq_files:
        if not file_path.exists():
            logger.warning(f"File not found, skipping: {file_path}")
            continue
        
        dest_path = output_dir / f"{file_path.name}.gz"
        logger.debug(f"Compressing {file_path} -> {dest_path}")
        
        # Use shutil to compress (gzip)
        # Note: shutil.compress is available in Python 3.12+, using gzip module for broader compatibility
        import gzip
        with open(file_path, 'rb') as f_in:
            with gzip.open(dest_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        if dest_path.exists():
            compressed_files.append(dest_path)
            logger.info(f"Compressed: {dest_path}")
        else:
            logger.error(f"Failed to create compressed file: {dest_path}")
            
    return compressed_files

def deposit_to_zenodo(compressed_files: list[Path], metadata: dict, zenodo_token: str, sandbox: bool = False) -> str:
    """
    Deposits compressed files to Zenodo using the zenodo_get CLI or API.
    This implementation uses the `zenodo_get` CLI tool which is robust for 
    command-line pipelines and handles authentication via environment variable.
    
    Args:
        compressed_files: List of Path objects to files to upload.
        metadata: Dictionary containing deposition metadata (title, description, etc).
        zenodo_token: Zenodo API token.
        sandbox: If True, use Zenodo Sandbox (Sandbox Zenodo).
        
    Returns:
        The Zenodo DOI string.
    """
    if not compressed_files:
        logger.error("No files to deposit to Zenodo.")
        raise ValueError("No files provided for Zenodo deposit.")
    
    if not zenodo_token:
        logger.error("ZENODO_TOKEN environment variable is not set.")
        raise EnvironmentError("ZENODO_TOKEN is required for Zenodo deposition.")
    
    # Prepare metadata JSON file for zenodo_get
    metadata_file = Path("zenodo_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Construct command
    # zenodo_get handles the upload and returns the DOI
    # We need to ensure the token is available to the process
    env = os.environ.copy()
    env["ZENODO_TOKEN"] = zenodo_token
    
    cmd = [
        "zenodo_get",
        "--metadata", str(metadata_file),
        "--no-upload-logs" # Reduce noise
    ]
    
    if sandbox:
        cmd.append("--sandbox")
        
    cmd.extend([str(f) for f in compressed_files])
    
    logger.info(f"Uploading to Zenodo: {cmd}")
    
    try:
        # Run zenodo_get
        # Note: zenodo_get prints the DOI to stdout. We capture it.
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output for DOI
        # zenodo_get typically outputs: "DOI: 10.5072/zenodo.XXXXXXX"
        output = result.stdout + result.stderr
        doi = None
        for line in output.split('\n'):
            if 'DOI' in line and '10.' in line:
                # Extract the DOI
                parts = line.split()
                for part in parts:
                    if part.startswith('10.'):
                        doi = part.strip(',')
                        break
                if doi:
                    break
        
        if not doi:
            # Fallback: try to find any 10.xxxxx/zenodo.xxxxx pattern
            import re
            match = re.search(r'(10\.\d+/zenodo\.\d+)', output)
            if match:
                doi = match.group(1)
        
        if not doi:
            logger.warning("Could not parse DOI from zenodo_get output. Check logs manually.")
            raise RuntimeError("Failed to retrieve DOI from Zenodo response.")
            
        logger.info(f"Successfully deposited to Zenodo. DOI: {doi}")
        return doi
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Zenodo upload failed: {e.stderr}")
        raise RuntimeError(f"Zenodo upload failed: {e.stderr}")
    finally:
        if metadata_file.exists():
            metadata_file.unlink()

def run_lifecycle_cycle(retention_days: int, data_dir: str = "data/raw", metadata_path: str = "data/metadata.json", sandbox: bool = False):
    """
    Executes one full lifecycle management cycle.
    
    1. Loads configuration.
    2. Finds FASTQ files older than retention_days.
    3. Compresses them.
    4. Deploys to Zenodo.
    5. Updates metadata.json with DOI.
    6. Deletes local files.
    
    Args:
        retention_days: Age threshold in days.
        data_dir: Root directory to scan for FASTQ files.
        metadata_path: Path to the global metadata.json file.
        sandbox: Use Zenodo Sandbox.
    """
    logger.info(f"Starting lifecycle cycle for retention period: {retention_days} days")
    
    # Load config for token and other settings if not passed
    config = load_environment_config()
    zenodo_token = os.getenv("ZENODO_TOKEN")
    if not zenodo_token:
        logger.critical("ZENODO_TOKEN not found in environment. Aborting lifecycle cycle.")
        return
        
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Data directory {data_path} does not exist. Nothing to process.")
        return

    # Find FASTQ files (support .fastq, .fq, .fastq.gz, .fq.gz)
    # We only process uncompressed ones to compress them first
    patterns = ["*.fastq", "*.fq"]
    candidate_files = []
    
    for pattern in patterns:
        candidate_files.extend(data_path.rglob(pattern))
    
    eligible_files = []
    for file_path in candidate_files:
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        if mtime < cutoff_date:
            eligible_files.append(file_path)
    
    if not eligible_files:
        logger.info("No FASTQ files found older than the retention period.")
        return

    logger.info(f"Found {len(eligible_files)} FASTQ files eligible for lifecycle management.")
    
    # Create a temporary directory for compressed files
    temp_compress_dir = data_path / "temp_compressed"
    temp_compress_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Compress
        compressed_files = compress_fastqs(eligible_files, temp_compress_dir)
        
        if not compressed_files:
            logger.error("Compression produced no files. Aborting.")
            return

        # Step 2: Prepare Metadata for Zenodo
        # Generate a unique title including timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zenodo_metadata = {
            "title": f"PRJ-002 Legacy FASTQ Archive - {timestamp}",
            "description": "Archived FASTQ files from the Primate Splicing Evolution pipeline, compressed and moved to long-term storage.",
            "creators": [{"name": "PRJ-002 Pipeline"}],
            "access_right": "restricted", # Or 'open' depending on policy
            "license": "CC-BY-4.0",
            "publication_date": datetime.now().strftime("%Y-%m-%d"),
            "keywords": ["primate", "splicing", "evolution", "archive"]
        }
        
        # Step 3: Deposit to Zenodo
        doi = deposit_to_zenodo(compressed_files, zenodo_metadata, zenodo_token, sandbox=sandbox)
        
        # Step 4: Update Global Metadata
        # Load existing metadata
        metadata_json = Path(metadata_path)
        existing_data = {}
        if metadata_json.exists():
            with open(metadata_json, 'r') as f:
                existing_data = json.load(f)
        
        # Append new record
        archive_record = {
            "doi": doi,
            "timestamp": datetime.now().isoformat(),
            "files_archived": [str(f) for f in compressed_files],
            "original_files": [str(f) for f in eligible_files],
            "retention_days": retention_days
        }
        
        if "archives" not in existing_data:
            existing_data["archives"] = []
        existing_data["archives"].append(archive_record)
        
        # Write back
        with open(metadata_json, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        logger.info(f"Updated {metadata_path} with new DOI: {doi}")
        
        # Step 5: Cleanup - Delete local files (originals and compressed)
        logger.info("Cleaning up local files...")
        for f in eligible_files:
            if f.exists():
                f.unlink()
                logger.debug(f"Deleted original: {f}")
        
        for f in compressed_files:
            if f.exists():
                f.unlink()
                logger.debug(f"Deleted compressed: {f}")
                
        if temp_compress_dir.exists():
            shutil.rmtree(temp_compress_dir)
            
        logger.info("Lifecycle cycle completed successfully.")
        
    except Exception as e:
        logger.error(f"Lifecycle cycle failed with error: {e}")
        # Clean up temp dir on failure if possible
        if temp_compress_dir.exists():
            shutil.rmtree(temp_compress_dir, ignore_errors=True)
        raise

def main():
    """
    Entry point for the lifecycle manager.
    Reads retention period from environment or config.
    """
    setup_logger()
    
    # Default retention: 30 days (configurable)
    retention_days = int(os.getenv("LIFECYCLE_RETENTION_DAYS", "30"))
    data_dir = os.getenv("DATA_DIR", "data/raw")
    metadata_path = os.getenv("METADATA_PATH", "data/metadata.json")
    sandbox = os.getenv("ZENODO_SANDBOX", "false").lower() == "true"
    
    try:
        run_lifecycle_cycle(
            retention_days=retention_days,
            data_dir=data_dir,
            metadata_path=metadata_path,
            sandbox=sandbox
        )
    except Exception as e:
        logger.critical(f"Lifecycle manager terminated: {e}")
        exit(1)

if __name__ == "__main__":
    main()
