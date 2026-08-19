"""
Schema Manager for T006: Define, write, and checksum schema files.
"""
import os
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

# Import existing utilities
from src.config import get_project_root
from src.utils import update_state_artifact_hashes

logger = logging.getLogger(__name__)

SCHEMAS = {
    "dataset.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Dataset Sample Schema",
        "description": "Schema for individual sample entities in the cancer biomarker discovery dataset.",
        "type": "object",
        "required": ["sample_id", "tumor_type", "response_label", "expression_vector"],
        "properties": {
            "sample_id": {
                "type": "string",
                "description": "Unique identifier for the sample (e.g., TCGA barcode or GEO sample ID)."
            },
            "tumor_type": {
                "type": "string",
                "description": "The cancer type or tissue of origin (e.g., BRCA, LUAD)."
            },
            "response_label": {
                "type": "string",
                "description": "Chemotherapy response classification (e.g., 'Responder', 'NonResponder', 'CR', 'PR', 'SD', 'PD')."
            },
            "expression_vector": {
                "type": "array",
                "description": "Normalized gene expression values (e.g., VST transformed counts).",
                "items": {"type": "number", "format": "float"},
                "minItems": 1
            }
        }
    },
    "model_output.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Model Output Schema",
        "description": "Schema for the output of the predictive model training process.",
        "type": "object",
        "required": ["cancer_type", "alpha", "lambda", "coefficients", "cross_val_auc"],
        "properties": {
            "cancer_type": {"type": "string", "description": "The specific tumor type this model was trained on."},
            "alpha": {"type": "number", "format": "float", "description": "Elastic net mixing parameter (alpha)."},
            "lambda": {"type": "number", "format": "float", "description": "Regularization strength (lambda)."},
            "coefficients": {
                "type": "object",
                "description": "Mapping of gene symbols to their learned coefficients.",
                "additionalProperties": {"type": "number", "format": "float"}
            },
            "cross_val_auc": {
                "type": "number", "format": "float", "minimum": 0.0, "maximum": 1.0,
                "description": "Area Under the Curve (AUC) from cross-validation."
            }
        }
    },
    "meta_analysis.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Meta Analysis Schema",
        "description": "Schema for meta-analysis results aggregating differential expression across tumor types.",
        "type": "object",
        "required": ["gene_symbol", "meta_p_value", "log2FC_mean", "selected"],
        "properties": {
            "gene_symbol": {"type": "string", "description": "Standardized gene symbol (HGNC)."},
            "meta_p_value": {"type": "number", "format": "float", "minimum": 0.0, "maximum": 1.0, "description": "Combined p-value from meta-analysis."},
            "log2FC_mean": {"type": "number", "format": "float", "description": "Mean log2 fold change across tumor types."},
            "selected": {"type": "boolean", "description": "Flag indicating if this gene was selected for the final predictive panel."}
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

def write_schemas() -> Dict[str, str]:
    """Write schema YAML files to the contracts directory and return checksums."""
    project_root = get_project_root()
    contracts_dir = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    checksums = {}

    for filename, content in SCHEMAS.items():
        file_path = contracts_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(content, f, default_flow_style=False, sort_keys=False)
        checksums[filename] = compute_sha256(file_path)
        logger.info(f"Wrote schema: {file_path} (SHA256: {checksums[filename][:16]}...)")

    return checksums

def update_state_with_schema_checksums(checksums: Dict[str, str]) -> None:
    """Update the project state file with schema checksums."""
    project_root = get_project_root()
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
    
    # Load existing state if it exists
    existing_hashes = {}
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            existing_state = yaml.safe_load(f) or {}
            existing_hashes = existing_state.get("artifact_hashes", {})
    
    # Update with new schema checksums
    for filename, checksum in checksums.items():
        existing_hashes[f"specs/001-chemo-biomarker-discovery/contracts/{filename}"] = checksum
    
    # Write updated state
    state_data = {
        "project_id": "PROJ-135-identifying-predictive-biomarkers-of-che",
        "artifact_hashes": existing_hashes
    }
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file: {state_file}")

def main() -> None:
    """Main entry point for T006."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starting T006: Schema generation and checksumming")
    
    # Step 1 & 2: Write schemas
    checksums = write_schemas()
    
    # Step 3: Compute checksums and update state
    update_state_with_schema_checksums(checksums)
    
    logger.info("T006 completed successfully.")

if __name__ == "__main__":
    main()
