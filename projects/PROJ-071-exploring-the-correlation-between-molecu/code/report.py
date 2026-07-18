import os
import sys
import json
import hashlib
import importlib.metadata
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def get_data_path():
    config = get_config()
    return Path(config.get("data_dir", "data"))

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_package_version(package_name: str) -> str:
    """
    Get the version of a package.
    """
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "Not found"

def collect_reproducibility_metadata() -> Dict[str, Any]:
    """
    Collect reproducibility metadata including versions, URLs, and hashes.
    """
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'packages': {
            'rdkit': get_package_version('rdkit'),
            'pandas': get_package_version('pandas'),
            'scikit-learn': get_package_version('scikit-learn'),
            'numpy': get_package_version('numpy'),
            'matplotlib': get_package_version('matplotlib'),
            'seaborn': get_package_version('seaborn'),
            'pyyaml': get_package_version('pyyaml'),
            'requests': get_package_version('requests'),
            'datasets': get_package_version('datasets')
        },
        'dataset_url': "Synthyra/FDA-Approved-Drugs",
        'retrieval_date': datetime.now().strftime('%Y-%m-%d'),
        'file_hashes': {}
    }
    
    # Calculate hashes for data files
    data_dir = get_data_path()
    raw_file = data_dir / "raw" / "fda_drugs.csv"
    processed_file = data_dir / "processed" / "merged_drugs.csv"
    analysis_file = data_dir / "processed" / "analysis_results.json"
    
    if raw_file.exists():
        metadata['file_hashes']['raw'] = calculate_file_hash(raw_file)
    if processed_file.exists():
        metadata['file_hashes']['processed'] = calculate_file_hash(processed_file)
    if analysis_file.exists():
        metadata['file_hashes']['analysis'] = calculate_file_hash(analysis_file)
    
    return metadata

def save_reproducibility_report(metadata: Dict[str, Any], output_path: Path):
    """
    Save reproducibility report to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved reproducibility report to {output_path}")

def append_reproducibility_to_markdown(metadata: Dict[str, Any], report_path: Path):
    """
    Append reproducibility metadata to the results report.
    """
    report_content = f"""
    # Reproducibility Report

    **Generated**: {metadata['timestamp']}

    ## Package Versions
    - RDKit: {metadata['packages']['rdkit']}
    - Pandas: {metadata['packages']['pandas']}
    - Scikit-learn: {metadata['packages']['scikit-learn']}
    - NumPy: {metadata['packages']['numpy']}
    - Matplotlib: {metadata['packages']['matplotlib']}
    - Seaborn: {metadata['packages']['seaborn']}
    - PyYAML: {metadata['packages']['pyyaml']}
    - Requests: {metadata['packages']['requests']}
    - Datasets: {metadata['packages']['datasets']}

    ## Dataset Information
    - URL: {metadata['dataset_url']}
    - Retrieval Date: {metadata['retrieval_date']}

    ## File Hashes
    - Raw Data: {metadata['file_hashes'].get('raw', 'Not found')}
    - Processed Data: {metadata['file_hashes'].get('processed', 'Not found')}
    - Analysis Results: {metadata['file_hashes'].get('analysis', 'Not found')}
    """
    
    with open(report_path, 'a') as f:
        f.write(report_content.strip())
    logger.info(f"Appended reproducibility metadata to {report_path}")

def main():
    config = get_config()
    logger.info("Starting report generation")
    
    # Collect metadata
    metadata = collect_reproducibility_metadata()
    
    # Save reproducibility report
    output_path = get_data_path() / "reproducibility_log.json"
    save_reproducibility_report(metadata, output_path)
    
    # Append to results report
    results_report_path = Path("results_report.md")
    if results_report_path.exists():
        append_reproducibility_to_markdown(metadata, results_report_path)
    else:
        logger.warning("Results report not found. Skipping append.")
    
    logger.info("Report generation complete")

if __name__ == "__main__":
    main()
