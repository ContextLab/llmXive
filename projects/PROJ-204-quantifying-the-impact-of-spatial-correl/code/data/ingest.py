import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import requests
import yaml
import json
from urllib.parse import urlparse

# Import from sibling modules as per API surface
from data.align import create_aligned_dataset
from preprocess.calibrate import apply_mask_to_dataset, detect_dead_pixels, detect_artifacts
from utils.config import get_config

__all__ = [
    "ingest_and_filter_dataset",
    "download_data",
    "align_maps",
    "mask_defects",
    "load_feasibility_status",
    "download_from_zenodo",
]

def load_feasibility_status(state_dir: Path) -> Dict[str, Any]:
    """
    Load the data feasibility status from the state directory.
    Expected file: state/data_feasibility_status.yaml
    """
    feasibility_path = state_dir / "data_feasibility_status.yaml"
    if not feasibility_path.exists():
        raise FileNotFoundError(f"Feasibility status file not found: {feasibility_path}")
    
    with open(feasibility_path, 'r') as f:
        return yaml.safe_load(f)

def download_file(url: str, dest_path: Path) -> Path:
    """
    Download a file from a URL to a destination path.
    Raises an exception if the download fails.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded: {url} -> {dest_path}")
        return dest_path
    except requests.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        raise

def download_from_zenodo(record_id: str, output_dir: Path, files: Optional[List[str]] = None) -> List[Path]:
    """
    Download files from a Zenodo record.
    Zenodo API: https://zenodo.org/api/records/{record_id}
    """
    api_url = f"https://zenodo.org/api/records/{record_id}"
    try:
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if 'files' not in data.get('files', []):
            # Try alternative structure
            files_list = data.get('files', [])
            if not files_list:
                raise ValueError(f"No files found in Zenodo record {record_id}")
        else:
            files_list = data['files']

        downloaded_paths = []
        for file_info in files_list:
            if files and file_info['key'] not in files:
                continue
            
            file_url = file_info['links']['self']
            filename = file_info['key']
            dest = output_dir / filename
            
            # Use Zenodo's download link if available, otherwise the API link
            download_url = file_info.get('links', {}).get('self', file_url)
            download_file(download_url, dest)
            downloaded_paths.append(dest)
        
        return downloaded_paths
    except Exception as e:
        logging.error(f"Failed to download from Zenodo {record_id}: {e}")
        raise

def download_data(urls: List[str], dest_dir: Path) -> List[Path]:
    """
    Download files from a list of URLs into ``dest_dir``.
    Uses the real download logic from download_file.
    """
    downloaded = []
    dest_dir.mkdir(parents=True, exist_ok=True)
    for url in urls:
        if not url:
            continue
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = f"file_{len(downloaded)}.npy"
        target = dest_dir / filename
        try:
            download_file(url, target)
            downloaded.append(target)
        except Exception as e:
            logging.warning(f"Skipping failed download {url}: {e}")
    return downloaded

def align_maps(map_paths: List[Path]) -> Dict[str, np.ndarray]:
    """
    Align a collection of elemental map files using the existing align module.
    """
    if not map_paths:
        raise ValueError("No map paths provided for alignment")
    
    # Group by sample directory (assuming structure: raw_dir/sample_id/element.npy)
    # The create_aligned_dataset expects raw_dir and list of filenames
    sample_dir = map_paths[0].parent
    element_files = [p.name for p in map_paths]
    
    # Use the existing API from code/data/align.py
    return create_aligned_dataset(sample_dir, element_files)

def mask_defects(aligned_maps: Dict[str, np.ndarray], threshold: float = 0.1) -> Dict[str, np.ndarray]:
    """
    Generate a mask for defective regions and apply it to each map.
    Uses the existing calibrate module for defect detection.
    """
    if not aligned_maps:
        return aligned_maps
    
    # Convert dict to list of (name, array) for calibrate module
    map_list = [(name, arr) for name, arr in aligned_maps.items()]
    
    # Detect dead pixels and artifacts
    dead_pixels = detect_dead_pixels(map_list, threshold=threshold)
    artifacts = detect_artifacts(map_list, threshold=threshold)
    
    # Apply mask
    masked_maps = apply_mask_to_dataset(map_list, dead_pixels, artifacts)
    
    # Return as dict
    return {name: arr for name, arr in masked_maps}

def ingest_and_filter_dataset(
    metadata_csv: Path,
    raw_dir: Path,
    output_csv: Path,
    performance_columns: List[str],
    state_dir: Optional[Path] = None,
) -> None:
    """
    Orchestrate the ingestion pipeline: read metadata, download maps,
    align them, mask defects, and write a unified CSV.
    
    This is the main entry point for T014c.
    
    Parameters
    ----------
    metadata_csv: Path
        CSV containing sample_id, performance metrics, and URLs for each element.
    raw_dir: Path
        Directory where raw map files will be stored.
    output_csv: Path
        Destination for the unified dataset CSV.
    performance_columns: List[str]
        Columns in the metadata that contain performance metrics.
    state_dir: Path, optional
        Directory containing state files (e.g., feasibility status).
    """
    logging.info("Starting ingestion pipeline for unified dataset")
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    # Load metadata
    if not metadata_csv.exists():
        raise FileNotFoundError(f"Metadata CSV not found: {metadata_csv}")
    
    df = pd.read_csv(metadata_csv)
    logging.info(f"Loaded {len(df)} samples from {metadata_csv}")
    
    # Filter rows missing performance metrics (pre-filter dataset)
    before_count = len(df)
    required_cols = ["sample_id"] + performance_columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in metadata: {missing_cols}")
    
    df = df.dropna(subset=performance_columns)
    logging.info(
        "Filtered %d samples missing performance metrics (kept %d)",
        before_count - len(df),
        len(df),
    )
    
    # Check feasibility status if state_dir provided
    if state_dir:
        try:
            feasibility = load_feasibility_status(state_dir)
            if feasibility.get("status") == "fail":
                logging.error("Data feasibility check failed. Aborting ingestion.")
                raise RuntimeError(f"Data feasibility failed: {feasibility.get('reason', 'Unknown')}")
        except FileNotFoundError:
            logging.warning("Feasibility status file not found, proceeding with caution")
    
    # Process each sample
    records = []
    element_keys = [col for col in df.columns if col.endswith("_url") or col.endswith("_uri")]
    
    for idx, row in df.iterrows():
        sample_id = row["sample_id"]
        logging.info(f"Processing sample {sample_id} ({idx+1}/{len(df)})")
        
        sample_dir = raw_dir / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        # Download elemental maps
        urls = []
        for key in element_keys:
            url = row.get(key)
            if url and pd.notna(url):
                urls.append(str(url))
        
        if not urls:
            logging.warning(f"No URLs found for sample {sample_id}, skipping")
            continue
        
        try:
            downloaded = download_data(urls, sample_dir)
            if not downloaded:
                logging.warning(f"No files downloaded for sample {sample_id}, skipping")
                continue
        except Exception as e:
            logging.error(f"Download failed for sample {sample_id}: {e}")
            continue
        
        # Identify map files (Pb, I, MA)
        map_files = []
        for elem in ["Pb", "I", "MA"]:
            # Look for .npy or .tif files matching element name
            for f in sample_dir.iterdir():
                if f.suffix.lower() in [".npy", ".tif", ".tiff"] and elem.lower() in f.name.lower():
                    map_files.append(f)
                    break
        
        if len(map_files) < 3:
            logging.warning(f"Incomplete map files for sample {sample_id} (found {len(map_files)}), skipping")
            continue
        
        # Align maps
        try:
            aligned = align_maps(map_files)
        except Exception as e:
            logging.error(f"Alignment failed for sample {sample_id}: {e}")
            continue
        
        # Mask defects
        try:
            masked = mask_defects(aligned, threshold=0.1)
        except Exception as e:
            logging.error(f"Defect masking failed for sample {sample_id}: {e}")
            continue
        
        # Save masked maps and record paths
        record = {"sample_id": sample_id}
        for elem, arr in masked.items():
            elem_upper = elem.upper() if len(elem) == 1 else elem
            save_path = sample_dir / f"{elem_upper}_masked.npy"
            np.save(save_path, arr)
            record[f"{elem_upper}_map_path"] = str(save_path)
        
        # Add performance metrics
        for col in performance_columns:
            record[col] = row[col]
        
        records.append(record)
    
    # Write unified dataset
    if not records:
        logging.warning("No valid samples processed, creating empty dataset")
        empty_df = pd.DataFrame(columns=["sample_id", "Pb_map_path", "I_map_path", "MA_map_path"] + performance_columns)
        empty_df.to_csv(output_csv, index=False)
    else:
        out_df = pd.DataFrame(records)
        out_df.to_csv(output_csv, index=False)
        logging.info(f"Unified dataset written to {output_csv} with {len(out_df)} samples")

def main():
    """
    Main entry point for running the ingestion pipeline.
    Usage: python -m code.data.ingest --config config.yaml
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest and filter perovskite dataset")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--metadata", type=str, help="Path to metadata CSV (overrides config)")
    parser.add_argument("--output", type=str, help="Path to output CSV (overrides config)")
    args = parser.parse_args()
    
    # Load config
    config = get_config(args.config)
    
    metadata_path = Path(args.metadata) if args.metadata else Path(config.get("metadata_csv", "data/raw/metadata.csv"))
    raw_dir = Path(config.get("raw_dir", "data/raw"))
    output_path = Path(args.output) if args.output else Path(config.get("output_csv", "data/processed/unified_dataset.csv"))
    state_dir = Path(config.get("state_dir", "state"))
    performance_cols = config.get("performance_columns", ["PCE", "J_sc", "V_oc"])
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/ingest.log")
        ]
    )
    
    # Run ingestion
    ingest_and_filter_dataset(
        metadata_csv=metadata_path,
        raw_dir=raw_dir,
        output_csv=output_path,
        performance_columns=performance_cols,
        state_dir=state_dir
    )

if __name__ == "__main__":
    main()
