import os
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

from src.config import get_project_root

logger = logging.getLogger(__name__)

SCHEMA_CONTENTS = {
    "dataset.schema.yaml": {
        "sample_id": {"type": "string", "description": "Unique identifier for the biological sample"},
        "tumor_type": {"type": "string", "description": "Type of tumor (e.g., BRCA, LUAD)"},
        "response_label": {"type": "string", "description": "Chemotherapy response label (e.g., CR, PR, SD, PD)"},
        "expression_vector": {
            "type": "array",
            "description": "Array of float values representing gene expression levels",
            "items": {"type": "float"}
        }
    },
    "model_output.schema.yaml": {
        "cancer_type": {"type": "string", "description": "The cancer type for which this model was trained"},
        "alpha": {"type": "float", "description": "Elastic net mixing parameter"},
        "lambda": {"type": "float", "description": "Regularization strength parameter"},
        "coefficients": {"type": "object", "description": "Mapping of gene symbols to their model coefficients"},
        "cross_val_auc": {"type": "float", "description": "Area Under the Curve from nested cross-validation"}
    },
    "meta_analysis.schema.yaml": {
        "gene_symbol": {"type": "string", "description": "Official HGNC gene symbol"},
        "meta_p_value": {"type": "float", "description": "P-value from meta-analysis (e.g., Stouffer's method)"},
        "log2FC_mean": {"type": "float", "description": "Mean log2 fold change across tumor types"},
        "selected": {"type": "boolean", "description": "Whether this gene was selected for the final panel"}
    }
}

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_schemas() -> Dict[str, Path]:
    """Write schema files to the contracts directory."""
    project_root = get_project_root()
    contracts_dir = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    written_files = {}
    for filename, content in SCHEMA_CONTENTS.items():
        file_path = contracts_dir / filename
        with open(file_path, "w") as f:
            yaml.dump(content, f, default_flow_style=False, sort_keys=False)
        written_files[filename] = file_path
        logger.info(f"Written schema: {file_path}")
    
    return written_files

def update_state_with_schema_checksums(schema_files: Dict[str, Path]) -> None:
    """Compute checksums for schema files and update the project state file."""
    project_root = get_project_root()
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
    
    current_hashes = {}
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                current_state = yaml.safe_load(f) or {}
                current_hashes = current_state.get("artifact_hashes", {})
        except Exception as e:
            logger.warning(f"Could not read existing state file: {e}")
    
    for filename, file_path in schema_files.items():
        checksum = compute_sha256(file_path)
        current_hashes[filename] = checksum
        logger.info(f"Computed checksum for {filename}: {checksum}")
    
    new_state = {
        "artifact_hashes": current_hashes
    }
    
    with open(state_file, "w") as f:
        yaml.dump(new_state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file: {state_file}")

def main():
    """Main entry point for schema generation and checksumming."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting schema generation and checksum computation...")
    
    schema_files = write_schemas()
    update_state_with_schema_checksums(schema_files)
    
    logger.info("Schema generation and checksum update completed successfully.")

if __name__ == "__main__":
    main()