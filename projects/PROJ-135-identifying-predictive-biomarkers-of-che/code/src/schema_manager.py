import os
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

from .config import get_project_root

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def write_schemas(schema_contents: Dict[str, str], output_dir: Path) -> None:
    """Write schema YAML files to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in schema_contents.items():
        file_path = output_dir / filename
        with open(file_path, "w") as f:
            f.write(content)
        logger.info(f"Wrote schema: {file_path}")

def update_state_with_schema_checksums(
    checksums: Dict[str, str], state_file_path: Path
) -> None:
    """Update the project state YAML file with schema checksums."""
    state_file_path.parent.mkdir(parents=True, exist_ok=True)

    if state_file_path.exists():
        with open(state_file_path, "r") as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state_data = {}
    else:
        state_data = {}

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    # Update with new checksums
    state_data["artifact_hashes"].update(checksums)

    with open(state_file_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state file with checksums: {state_file_path}")

def main() -> None:
    """Main entry point for schema management and checksum computation."""
    logging.basicConfig(level=logging.INFO)
    project_root = get_project_root()

    # Define schema contents (from T006a)
    schema_contents = {
        "dataset.schema.yaml": """
fields:
  - name: sample_id
    type: string
  - name: tumor_type
    type: string
  - name: response_label
    type: string
  - name: expression_vector
    type: array
    items: float
""",
        "model_output.schema.yaml": """
fields:
  - name: cancer_type
    type: string
  - name: alpha
    type: float
  - name: lambda
    type: float
  - name: coefficients
    type: object
  - name: cross_val_auc
    type: float
""",
        "gene_panel.schema.yaml": """
fields:
  - name: gene_symbol
    type: string
  - name: meta_p_value
    type: float
  - name: log2FC_mean
    type: float
  - name: selected
    type: boolean
""",
        "aggregate_significance_resolved.schema.yaml": """
fields:
  - name: gene_symbol
    type: string
  - name: tumor_type
    type: string
  - name: p_value
    type: float
""",
    }

    contracts_dir = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts"
    state_dir = project_root / "state" / "projects"

    # Write schemas
    write_schemas(schema_contents, contracts_dir)

    # Compute checksums
    checksums = {}
    for filename in schema_contents.keys():
        file_path = contracts_dir / filename
        checksums[filename] = compute_sha256(file_path)
        logger.info(f"Computed checksum for {filename}: {checksums[filename]}")

    # Update state file
    state_file_path = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
    update_state_with_schema_checksums(checksums, state_file_path)

    logger.info("Schema management and checksum computation completed successfully.")

if __name__ == "__main__":
    main()