"""
Schema Manager: Defines, writes, and checksums schema files for the project.
Implements T006: Schema files and checksums.
"""
import os
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

from src.config import get_project_root, ensure_directories

logger = logging.getLogger(__name__)

# Schema definitions matching T006 requirements
DATASET_SCHEMA = """
# Schema for processed dataset samples
# Defines the structure of individual sample records in the discovery/training sets
fields:
  - name: sample_id
    type: string
    description: Unique identifier for the sample (e.g., TCGA barcode or GEO sample ID)
    required: true
  - name: tumor_type
    type: string
    description: Cancer type classification (e.g., BRCA, LUAD)
    required: true
  - name: response_label
    type: string
    description: Chemotherapy response status (e.g., 'Responder', 'NonResponder')
    required: true
  - name: expression_vector
    type: array
    item_type: float
    description: Normalized expression values for the gene panel, ordered by gene symbol
    required: true
metadata:
  version: "1.0"
  source: llmXive pipeline T006
  format: YAML
"""

MODEL_OUTPUT_SCHEMA = """
# Schema for predictive model outputs
# Defines the structure of model artifacts saved after training and validation
fields:
  - name: cancer_type
    type: string
    description: The specific tumor type this model was trained on
    required: true
  - name: alpha
    type: float
    description: Elastic net mixing parameter (0=Lasso, 1=Ridge)
    required: true
  - name: lambda
    type: float
    description: Elastic net regularization strength (lambda.min or lambda.1se)
    required: true
  - name: coefficients
    type: object
    description: Map of gene_symbol -> coefficient value
    required: true
  - name: cross_val_auc
    type: float
    description: Mean AUC from nested cross-validation
    required: true
metadata:
  version: "1.0"
  source: llmXive pipeline T006
  format: YAML
"""

GENE_PANEL_SCHEMA = """
# Schema for the final selected gene panel
# Defines the structure of biomarkers identified through meta-analysis
fields:
  - name: gene_symbol
    type: string
    description: HGNC approved gene symbol
    required: true
  - name: meta_p_value
    type: float
    description: Combined p-value from Stouffer's meta-analysis
    required: true
  - name: log2FC_mean
    type: float
    description: Mean log2 fold change across tumor types
    required: true
  - name: selected
    type: boolean
    description: Whether this gene was included in the final panel (True/False)
    required: true
metadata:
  version: "1.0"
  source: llmXive pipeline T006
  format: YAML
"""

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_schemas() -> Dict[str, Path]:
    """
    Write schema files to the contracts directory.
    Returns a dict mapping schema name to file path.
    """
    project_root = get_project_root()
    contracts_dir = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    ensure_directories([contracts_dir])

    schemas = {
        "dataset": DATASET_SCHEMA,
        "model_output": MODEL_OUTPUT_SCHEMA,
        "gene_panel": GENE_PANEL_SCHEMA
    }

    written_paths = {}
    for name, content in schemas.items():
        file_path = contracts_dir / f"{name}.schema.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        written_paths[name] = file_path
        logger.info(f"Written schema: {file_path}")

    return written_paths

def update_state_with_schema_checksums(schema_paths: Dict[str, Path]) -> None:
    """
    Compute checksums for schema files and write them to the project state file.
    Updates state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml
    """
    project_root = get_project_root()
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
    
    ensure_directories([state_dir])

    artifact_hashes = {}
    for name, path in schema_paths.items():
        checksum = compute_sha256(path)
        artifact_hashes[f"schema/{name}"] = checksum
        logger.info(f"Computed checksum for {name}: {checksum}")

    # Load existing state if present, or create new
    state_data = {}
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}")

    # Update artifact_hashes
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    state_data["artifact_hashes"].update(artifact_hashes)

    # Write updated state
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file: {state_file}")

def main() -> None:
    """Main entry point for T006."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Starting T006: Implement schema files and checksums")
    
    # Step 1: Write schema files
    schema_paths = write_schemas()
    
    # Step 2: Compute checksums and update state
    update_state_with_schema_checksums(schema_paths)
    
    logger.info("T006 completed successfully")

if __name__ == "__main__":
    main()