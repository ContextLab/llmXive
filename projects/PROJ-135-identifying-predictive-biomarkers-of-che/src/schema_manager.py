import os
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

from src.config import get_project_root

logger = logging.getLogger(__name__)

SCHEMAS = {
    "dataset": {
        "type": "object",
        "required": ["sample_id", "tumor_type", "response_label", "expression_vector"],
        "properties": {
            "sample_id": {"type": "string", "description": "Unique identifier for the sample"},
            "tumor_type": {"type": "string", "description": "Cancer type classification (e.g., BRCA, LUAD)"},
            "response_label": {"type": "string", "description": "Clinical response outcome (e.g., 'Responder', 'NonResponder')"},
            "expression_vector": {
                "type": "array",
                "description": "Normalized gene expression values (VST or similar)",
                "items": {"type": "number", "format": "float"}
            }
        }
    },
    "model_output": {
        "type": "object",
        "required": ["cancer_type", "alpha", "lambda", "coefficients", "cross_val_auc"],
        "properties": {
            "cancer_type": {"type": "string", "description": "Tumor type the model was trained on"},
            "alpha": {"type": "number", "format": "float", "description": "Elastic net mixing parameter"},
            "lambda": {"type": "number", "format": "float", "description": "Elastic net regularization parameter"},
            "coefficients": {
                "type": "object",
                "description": "Mapping of gene symbols to their model coefficients",
                "additionalProperties": {"type": "number", "format": "float"}
            },
            "cross_val_auc": {"type": "number", "format": "float", "description": "Area Under Curve from cross-validation"}
        }
    },
    "gene_panel": {
        "type": "object",
        "required": ["gene_symbol", "meta_p_value", "log2FC_mean", "selected"],
        "properties": {
            "gene_symbol": {"type": "string", "description": "HGNC gene symbol"},
            "meta_p_value": {"type": "number", "format": "float", "description": "Combined p-value from meta-analysis"},
            "log2FC_mean": {"type": "number", "format": "float", "description": "Mean log2 fold change across tumor types"},
            "selected": {"type": "boolean", "description": "Whether the gene is included in the final panel"}
        }
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
    """Write schema definitions to contract directory."""
    project_root = get_project_root()
    contracts_dir = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    written_files = {}
    for name, schema in SCHEMAS.items():
        file_path = contracts_dir / f"{name}.schema.yaml"
        with open(file_path, "w") as f:
            yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
        written_files[name] = file_path
        logger.info(f"Written schema: {file_path}")
    
    return written_files

def update_state_with_schema_checksums() -> None:
    """Compute checksums for schema files and update state file."""
    project_root = get_project_root()
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"

    contracts_dir = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    schema_files = [
        contracts_dir / "dataset.schema.yaml",
        contracts_dir / "model_output.schema.yaml",
        contracts_dir / "gene_panel.schema.yaml"
    ]

    artifact_hashes = {}
    for schema_file in schema_files:
        if schema_file.exists():
          checksum = compute_sha256(schema_file)
          artifact_hashes[schema_file.name] = checksum
          logger.info(f"Checksum for {schema_file.name}: {checksum}")
        else:
            logger.warning(f"Schema file not found: {schema_file}")

    state_data = {}
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f) or {}

    state_data["artifact_hashes"] = artifact_hashes

    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file: {state_file}")

def main():
    """Main entry point for schema generation and checksumming."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting schema generation and checksumming...")
    write_schemas()
    update_state_with_schema_checksums()
    logger.info("Schema generation and checksumming complete.")

if __name__ == "__main__":
    main()
