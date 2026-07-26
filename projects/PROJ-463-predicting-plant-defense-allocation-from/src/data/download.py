"""
Module for downloading FASTQ files from NCBI GEO/SRA.
Implements real data fetching with strict failure policies.
"""
import os
import sys
import json
import hashlib
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json as json_lib

# Import from project utils
from src.utils.config import get_data_path, get_config
from src.utils.logger import get_logger
from src.utils.schemas import RNASeqStudy, DataManifest, ManifestEntry, ProvenanceInfo
from src.utils.provenance import record_provenance, ArtifactType

logger = get_logger(__name__)

# SRA Toolkit command path (assumes it's in PATH or configured)
SRABIN = "prefetch"
FASTQDUMP = "fasterq-dump"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_sra_accession_info(accession_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for an SRA accession from NCBI E-utilities.
    Returns a dict with run info, fastq URLs, etc.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = f"db=sra&id={accession_id}&rettype=json"
    url = f"{base_url}?{params}"
    
    try:
        req = Request(url, headers={'User-Agent': 'llmXive-pipeline/1.0'})
        with urlopen(req, timeout=30) as response:
            data = json_lib.loads(response.read().decode('utf-8'))
            return data
    except (URLError, HTTPError, json_lib.JSONDecodeError) as e:
        logger.error(f"Failed to fetch SRA info for {accession_id}: {e}")
        raise RuntimeError(f"Failed to fetch SRA metadata for {accession_id}") from e

def get_fastq_download_url(accession_id: str, run_id: str) -> str:
    """
    Construct the direct FTP/HTTP URL for FASTQ download.
    Uses NCBI SRA FTP server structure.
    """
    # Standard NCBI SRA FTP structure
    ftp_base = "ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByRun/sra"
    # Construct path: /S/R/<RunID up to 3 chars>/<RunID>/
    # Example: SRR123 -> /S/R/123/SRR123/SRR123.sra
    # But we want fastq, usually available via fasterq-dump or direct FTP if public
    
    # For direct download, we often need to use the SRA Toolkit or specific URLs.
    # A common pattern for public data is:
    # https://sra-download.ncbi.nlm.nih.gov/traces/sra/<year>/<run_prefix>/<run_id>/<run_id>.sra
    
    # Let's try to get the actual run info to find the file path
    info = fetch_sra_accession_info(accession_id)
    
    # Extract run list
    runs = []
    if 'result' in info and 'run' in info['result']:
        run_list = info['result']['run']
        for r in run_list:
            if r.get('accession') == run_id:
                runs.append(r)
                break
    
    if not runs:
        # Fallback: try to find any run
        if 'result' in info and 'run' in info['result']:
            for r in info['result']['run']:
                if r.get('accession').startswith(run_id[:3]): # Approximate match
                     runs.append(r)
                     break

    if not runs:
        raise ValueError(f"Could not locate run {run_id} in SRA metadata for {accession_id}")
    
    run_info = runs[0]
    # Construct FTP path
    # Example: ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByRun/sra/SRR/SRR123/SRR123.sra
    # We need the .sra file path to run fasterq-dump on it, or direct fastq if available.
    # NCBI often requires running fasterq-dump on the .sra file.
    
    # Let's return the base SRA file path for processing
    # Format: /<RunID>/<RunID>.sra
    run_prefix = run_id[:3]
    sra_file = f"{run_id}/{run_id}.sra"
    full_path = f"sra/{run_prefix}/{sra_file}"
    
    return f"ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByRun/sra/{full_path}"

def download_file_with_progress(url: str, output_path: Path, chunk_size: int = 8192) -> None:
    """Download a file with progress logging."""
    logger.info(f"Downloading from {url} to {output_path}")
    try:
        req = Request(url, headers={'User-Agent': 'llmXive-pipeline/1.0'})
        with urlopen(req, timeout=120) as response:
            total_size = int(response.getheader('Content-Length', 0))
            downloaded = 0
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

def download_fastq_from_sra(accession_id: str, run_id: str, output_dir: Path) -> List[Path]:
    """
    Download FASTQ files for a given SRA run.
    Uses fasterq-dump from SRA toolkit if direct download fails or is not applicable.
    Returns list of downloaded FASTQ file paths.
    """
    logger.info(f"Processing SRA run {run_id} for accession {accession_id}")
    
    # Check if fasterq-dump is available
    try:
        subprocess.run([FASTQDUMP, '--version'], check=True, capture_output=True, timeout=5)
    except (subprocess.SubprocessError, FileNotFoundError):
        raise RuntimeError(f"{FASTQDUMP} not found. Please install SRA Toolkit.")
    
    # Create temp dir for SRA file if needed
    sra_file_path = output_dir / f"{run_id}.sra"
    fastq_files = []
    
    # Strategy: Try to get .sra file, then convert to fastq
    # 1. Check if .sra exists locally (from previous run)
    if not sra_file_path.exists():
        # 2. Try to download .sra
        sra_url = get_fastq_download_url(accession_id, run_id)
        try:
            download_file_with_progress(sra_url, sra_file_path)
        except Exception as e:
            logger.warning(f"Direct SRA download failed for {run_id}: {e}")
            # If direct download fails, we might need to use prefetch
            logger.info(f"Attempting prefetch for {run_id}")
            try:
                subprocess.run([SRABIN, run_id], check=True, timeout=300, cwd=output_dir)
                # prefetch usually downloads to a specific location in SRA db, 
                # but we need the local file. This is tricky without knowing SRA lib path.
                # Fallback: raise error if we can't get the file
                raise RuntimeError("Prefetch also failed or path unknown")
            except Exception as pref_e:
                logger.error(f"Prefetch failed: {pref_e}")
                raise RuntimeError(f"Failed to obtain SRA file for {run_id}")
    
    # 3. Convert SRA to FASTQ
    # fasterq-dump output
    output_prefix = output_dir / run_id
    cmd = [
        FASTQDUMP,
        '--split-files', # Split paired ends
        '--gzip',        # Compress output
        '--outdir', str(output_dir),
        str(sra_file_path)
    ]
    
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        # fasterq-dump creates files like {run_id}_1.fastq.gz, {run_id}_2.fastq.gz
        # Find them
        fastq_files = list(output_dir.glob(f"{run_id}_*.fastq.gz"))
        if not fastq_files:
            # Maybe single end
            fastq_files = list(output_dir.glob(f"{run_id}.fastq.gz"))
        
        if not fastq_files:
            raise RuntimeError(f"No FASTQ files generated for {run_id}")
        
        logger.info(f"Generated FASTQ files: {[str(f) for f in fastq_files]}")
        return fastq_files
        
    except subprocess.CalledProcessError as e:
        logger.error(f"fasterq-dump failed: {e.stderr}")
        raise RuntimeError(f"Failed to convert SRA to FASTQ for {run_id}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout converting SRA to FASTQ for {run_id}")

def fetch_geosamples_study(study_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a GEO study using E-utilities.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = f"db=gds&id={study_id}&rettype=json"
    url = f"{base_url}?{params}"
    
    try:
        req = Request(url, headers={'User-Agent': 'llmXive-pipeline/1.0'})
        with urlopen(req, timeout=30) as response:
            data = json_lib.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        logger.error(f"Failed to fetch GEO study info for {study_id}: {e}")
        raise RuntimeError(f"Failed to fetch GEO metadata for {study_id}") from e

def create_manifest_entry(
    file_path: Path,
    accession_id: str,
    run_id: str,
    source_type: str = "real"
) -> ManifestEntry:
    """Create a manifest entry for a downloaded file."""
    checksum = calculate_sha256(file_path)
    return ManifestEntry(
        file_name=str(file_path),
        checksum=checksum,
        source_type=source_type,
        provenance=ProvenanceInfo(
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            accession_id=accession_id,
            run_id=run_id,
            organism="Unknown", # To be filled by metadata
            tool_versions={"fasterq-dump": "unknown"} # Could parse version
        )
    )

def save_manifest(manifest: DataManifest, output_path: Path) -> None:
    """Save the manifest to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(manifest.model_dump(), f, indent=2)
    logger.info(f"Manifest saved to {output_path}")

def validate_downloaded_files(files: List[Path]) -> bool:
    """Basic validation that files are non-empty and readable."""
    for f in files:
        if not f.exists():
            logger.error(f"File {f} does not exist")
            return False
        if f.stat().st_size == 0:
            logger.error(f"File {f} is empty")
            return False
    return True

def download_study(accession_id: str, run_id: str, output_dir: Path) -> Tuple[List[Path], ManifestEntry]:
    """
    Download FASTQ files for a specific study/run.
    Returns list of file paths and the manifest entry.
    """
    logger.info(f"Downloading study {accession_id}, run {run_id}")
    
    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download
    fastq_files = download_fastq_from_sra(accession_id, run_id, output_dir)
    
    if not validate_downloaded_files(fastq_files):
        raise RuntimeError("Download validation failed")
    
    # Create manifest entry (using the first file as representative, or aggregate?)
    # For simplicity, we create one entry per file, but the task asks for a manifest of the study.
    # Let's create an entry for the first file and note the others in the manifest or create multiple.
    # The schema allows a list of entries. We'll return the list.
    
    entries = []
    for f in fastq_files:
        entry = create_manifest_entry(f, accession_id, run_id)
        entries.append(entry)
    
    return fastq_files, entries

def main():
    """
    CLI entry point for downloading.
    Usage: python -m src.data.download --accession GEO12345 --run SRR123456 --mode real
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download FASTQ files from NCBI SRA/GEO")
    parser.add_argument("--accession", type=str, required=True, help="GEO/SRA accession ID")
    parser.add_argument("--run", type=str, required=True, help="SRA Run ID (e.g., SRR...)")
    parser.add_argument("--mode", type=str, default="real", choices=["real", "synthetic"],
                      help="Mode: real (fetch from NCBI) or synthetic (use local synthetic data)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    
    args = parser.parse_args()
    
    config = get_config()
    data_path = Path(config.get_data_path())
    raw_dir = data_path / "raw"
    
    if args.output_dir:
        raw_dir = Path(args.output_dir)
    
    if args.mode == "synthetic":
        logger.warning("Synthetic mode requested. Loading from data/synthetic instead of downloading.")
        # In synthetic mode, we don't download, but we might load a pre-generated file.
        # This task is primarily for real download. Synthetic loading is handled by T015.
        # We will raise an error if no synthetic data is found, as per "Fail loudly" constraint.
        synthetic_dir = data_path / "synthetic"
        if not synthetic_dir.exists():
            raise FileNotFoundError("Synthetic mode requested but data/synthetic directory not found.")
        
        # Find a synthetic file
        synth_files = list(synthetic_dir.glob("*.fastq.gz"))
        if not synth_files:
            raise FileNotFoundError("Synthetic mode requested but no FASTQ files found in data/synthetic.")
        
        # Copy one to raw for consistency
        target_file = raw_dir / f"{args.run}.fastq.gz"
        import shutil
        shutil.copy2(synth_files[0], target_file)
        entry = create_manifest_entry(target_file, args.accession, args.run, source_type="synthetic")
        manifest = DataManifest(
            entries=[entry],
            study_id=args.accession,
            run_id=args.run
        )
        manifest_path = data_path / "manifests" / f"{args.accession}_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        save_manifest(manifest, manifest_path)
        return

    # Real mode
    try:
        files, entries = download_study(args.accession, args.run, raw_dir)
        
        # Create manifest
        manifest = DataManifest(
            entries=entries,
            study_id=args.accession,
            run_id=args.run
        )
        
        manifest_dir = data_path / "manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"{args.accession}_manifest.json"
        
        save_manifest(manifest, manifest_path)
        
        logger.info(f"Successfully downloaded {len(files)} files for {args.accession}")
        
    except Exception as e:
        logger.error(f"Failed to download real data: {e}")
        # Per constraint: Fail loudly, never silently.
        raise SystemExit(f"Real data fetch failed: {e}")

if __name__ == "__main__":
    main()