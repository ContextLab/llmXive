import os
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

from src.config import get_project_root

logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_schemas() -> None:
    """Write schema definitions to the contracts directory."""
    root = get_project_root()
    contracts_dir = root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    schemas = {
        "dataset.schema.yaml": """type: object
required:
  - sample_id
  - tumor_type
  - response_label
  - expression_vector
properties:
  sample_id:
    type: string
  tumor_type:
    type: string
  response_label:
    type: string
  expression_vector:
    type: array
    items:
type: number
""",
        "model_output.schema.yaml": """type: object
required:
  - cancer_type
  - alpha
  - lambda
  - coefficients
  - cross_val_auc
properties:
  cancer_type:
    type: string
  alpha:
    type: number
  lambda:
    type: number
  coefficients:
    type: object
  cross_val_auc:
    type: number
""",
        "gene_panel.schema.yaml": """type: object
required:
  - gene_symbol
  - meta_p_value
  - log2FC_mean
  - selected
properties:
  gene_symbol:
    type: string
  meta_p_value:
    type: number
  log2FC_mean:
    type: number
  selected:
    type: boolean
""",
        "aggregate_significance_resolved.schema.yaml": """type: object
required:
  - gene_symbol
  - tumor_type
  - p_value
properties:
  gene_symbol:
    type: string
  tumor_type:
    type: string
  p_value:
    type: number
"""
    }

    for filename, content in schemas.items():
        file_path = contracts_dir / filename
        with open(file_path, "w") as f:
            f.write(content)
        logger.info(f"Wrote schema: {file_path}")

def update_state_with_schema_checksums() -> None:
    """Compute checksums and update state file."""
    root = get_project_root()
    contracts_dir = root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    state_file = root / "state" / "projects" / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
    
    state_file.parent.mkdir(parents=True, exist_ok=True)

    checksums = {}
    if contracts_dir.exists():
        for schema_file in contracts_dir.glob("*.yaml"):
            checksums[schema_file.name] = compute_sha256(str(schema_file))

    # Load existing state or create new
    state_data = {}
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f) or {}

    state_data["artifact_hashes"] = state_data.get("artifact_hashes", {})
    state_data["artifact_hashes"]["schemas"] = checksums

    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False)

    logger.info(f"Updated state file with schema checksums: {state_file}")

def main() -> None:
    """Entry point for schema management."""
    logging.basicConfig(level=logging.INFO)
    write_schemas()
    update_state_with_schema_checksums()

if __name__ == "__main__":
    main()