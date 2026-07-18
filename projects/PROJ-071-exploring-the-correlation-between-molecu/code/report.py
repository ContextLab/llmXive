import os
import sys
import json
import hashlib
import importlib.metadata
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import get_config
from logging_config import get_logger

# Use config for paths
def get_data_path(relative_path: str) -> Path:
    config = get_config()
    return Path(config.get("data_dir", "data")) / relative_path

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculates SHA256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_package_version(package_name: str) -> str:
    """
    Gets version of a package.
    """
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "Unknown"

def collect_reproducibility_metadata() -> Dict[str, Any]:
    """
    Collects reproducibility metadata.
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
            'scipy': get_package_version('scipy'),
            'statsmodels': get_package_version('statsmodels')
        },
        'data_files': {}
    }
    
    # Add file hashes
    data_dir = get_data_path("")
    for file in data_dir.glob("**/*"):
        if file.is_file():
            metadata['data_files'][str(file)] = calculate_file_hash(file)
    
    return metadata

def save_reproducibility_report(metadata: Dict[str, Any], output_path: Path):
    """
    Saves reproducibility report to JSON.
    """
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def append_reproducibility_to_markdown(metadata: Dict[str, Any], report_path: Path):
    """
    Appends reproducibility metadata to markdown report.
    """
    with open(report_path, 'a') as f:
        f.write("\n## Reproducibility Information\n\n")
        f.write(f"- **Timestamp**: {metadata['timestamp']}\n\n")
        f.write("### Package Versions\n\n")
        for pkg, ver in metadata['packages'].items():
            f.write(f"- {pkg}: {ver}\n")
        f.write("\n### Data File Hashes\n\n")
        for file, hash_val in metadata['data_files'].items():
            f.write(f"- `{file}`: {hash_val}\n")

def main():
    """
    Main entry point for report generation.
    """
    logger = get_logger(__name__)
    logger.info("Starting report generation...")
    
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    outputs_dir = data_dir / "outputs"
    
    # Collect metadata
    metadata = collect_reproducibility_metadata()
    
    # Save JSON report
    json_path = data_dir / "reproducibility_log.json"
    save_reproducibility_report(metadata, json_path)
    
    # Generate markdown report
    md_path = data_dir.parent / "results_report.md"
    with open(md_path, 'w') as f:
        f.write("# Research Results Report\n\n")
        f.write("## Summary\n\n")
        f.write("This report summarizes the correlation analysis between molecular complexity and degradation rates.\n\n")
        f.write("## Methodology\n\n")
        f.write("- Data sourced from HuggingFace: Synthyra/FDA-Approved-Drugs\n")
        f.write("- Molecular descriptors calculated using RDKit\n")
        f.write("- Correlation analysis performed using Pearson and Spearman methods\n")
        f.write("- Regression models: MLR and LASSO with K=5 cross-validation\n\n")
        
        # Append reproducibility info
        append_reproducibility_to_markdown(metadata, md_path)
    
    logger.info(f"Report generated at {md_path}")
    logger.info(f"Reproducibility log saved at {json_path}")

if __name__ == "__main__":
    main()
