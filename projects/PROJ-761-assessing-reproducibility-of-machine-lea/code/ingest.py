import csv
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/logs/ingest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import jsonschema, if not available, implement a basic validator or warn
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logger.warning("jsonschema not installed. Validation will be skipped or basic checks only.")

class PaperManifest:
    """Data class representing a validated paper manifest entry."""
    def __init__(self, data: Dict[str, Any]):
        self.doi = data.get('doi')
        self.title = data.get('title')
        self.authors = data.get('authors', [])
        self.year = data.get('year')
        self.dataset_name = data.get('dataset_name')
        self.repo_url = data.get('repo_url')
        self.reported_metrics = data.get('reported_metrics', {})
        self.experimental_replicates = data.get('experimental_replicates')
        self.reaction_conditions = data.get('reaction_conditions')
        self.notes = data.get('notes')
        self.raw_data = data

    def to_dict(self) -> Dict[str, Any]:
        return self.raw_data

    def __repr__(self):
        return f"PaperManifest(doi={self.doi}, title={self.title[:30]}...)"

def load_manifest_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load manifest from a CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest CSV not found: {csv_path}")
    
    manifests = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types where necessary
            # Expecting CSV to have flat structure, nested objects might be JSON strings
            if 'reported_metrics' in row and isinstance(row['reported_metrics'], str):
                try:
                    row['reported_metrics'] = json.loads(row['reported_metrics'])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse reported_metrics for {row.get('doi')}: {row['reported_metrics']}")
                    row['reported_metrics'] = {}
            
            if 'reaction_conditions' in row and isinstance(row['reaction_conditions'], str):
                try:
                    row['reaction_conditions'] = json.loads(row['reaction_conditions'])
                except json.JSONDecodeError:
                    row['reaction_conditions'] = {}

            if 'experimental_replicates' in row:
                try:
                    row['experimental_replicates'] = int(row['experimental_replicates'])
                except (ValueError, TypeError):
                    row['experimental_replicates'] = None

            manifests.append(row)
    return manifests

def load_manifest_yaml(yaml_path: str) -> List[Dict[str, Any]]:
    """Load manifest from a YAML file."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest YAML not found: {yaml_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'papers' in data:
        return data['papers']
    else:
        raise ValueError(f"Unexpected YAML structure in {yaml_path}")

def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Load manifest from CSV or YAML based on extension."""
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    suffix = path.suffix.lower()
    if suffix == '.csv':
        return load_manifest_csv(manifest_path)
    elif suffix in ['.yaml', '.yml']:
        return load_manifest_yaml(manifest_path)
    else:
        raise ValueError(f"Unsupported manifest format: {suffix}")

def validate_manifest(manifests: List[Dict[str, Any]], schema_path: str) -> List[PaperManifest]:
    """
    Validate a list of manifest dictionaries against a JSON Schema.
    Returns a list of validated PaperManifest objects.
    Raises an exception if validation fails (Blocking).
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_file, 'r') as f:
        schema = yaml.safe_load(f)

    validated_results = []
    
    if not HAS_JSONSCHEMA:
        logger.error("jsonschema library is required for validation but is not installed.")
        raise ImportError("Missing 'jsonschema' dependency. Run: pip install jsonschema")

    for i, entry in enumerate(manifests):
        try:
            jsonschema.validate(instance=entry, schema=schema)
            pm = PaperManifest(entry)
            validated_results.append(pm)
            logger.info(f"Validated entry {i+1}: {pm.doi}")
        except jsonschema.ValidationError as e:
            error_msg = f"Validation failed for entry {i+1} (DOI: {entry.get('doi', 'Unknown')}): {e.message}"
            logger.error(error_msg)
            # Blocking: Halt execution on validation failure as per task spec
            raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error processing entry {i+1}: {e}")
            raise

    return validated_results

def fetch_dataset(dataset_name: str) -> str:
    """
    Placeholder for fetching dataset. 
    In a real implementation, this would download data based on dataset_name.
    For T003, we assume data is already in data/raw or data/processed.
    """
    # Check common locations
    possible_paths = [
        f"data/raw/{dataset_name}",
        f"data/processed/{dataset_name}",
        f"data/raw/{dataset_name}.csv",
        f"data/processed/{dataset_name}.csv"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"Dataset '{dataset_name}' not found in expected locations.")

def find_supplementary_files(doi: str) -> List[str]:
    """Find supplementary files for a given DOI."""
    # Implementation would search data/raw/supplementary/
    # Returning empty list for now as T003 focuses on validation
    return []

def parse_pdf_for_metadata(pdf_path: str) -> Dict[str, Any]:
    """Extract metadata from a PDF if needed."""
    # Placeholder
    return {}

def parse_csv_for_metadata(csv_path: str) -> Dict[str, Any]:
    """Extract metadata from a CSV if needed."""
    # Placeholder
    return {}

def process_manifest_entry(entry: Dict[str, Any]) -> PaperManifest:
    """Process a single manifest entry into a PaperManifest object."""
    return PaperManifest(entry)

def verify_dataset_variables(manifest: PaperManifest) -> bool:
    """Verify that required variables exist in the dataset."""
    # Placeholder for T015 logic
    return True

def ingest_pipeline(manifest_path: str, schema_path: str) -> List[PaperManifest]:
    """
    Main pipeline: Load manifest from CSV/YAML and validate against schema.
    """
    logger.info(f"Starting ingestion pipeline for {manifest_path}")
    manifests = load_manifest(manifest_path)
    logger.info(f"Loaded {len(manifests)} entries")
    validated_manifests = validate_manifest(manifests, schema_path)
    logger.info(f"Successfully validated {len(validated_manifests)} entries")
    return validated_manifests

def main():
    """Entry point for CLI execution."""
    # Default paths relative to project root
    manifest_path = "data/manifest.csv"
    schema_path = "contracts/PaperManifest.schema.yaml"

    # Allow override via environment or args if needed, but for T003 we use defaults
    if not os.path.exists(manifest_path):
        logger.error(f"Manifest file not found: {manifest_path}")
        # If manifest doesn't exist, we can't validate. 
        # However, T003 implies the manifest exists but needs validation against schema.
        # If the task is to create the schema and validate, we assume manifest exists.
        # If it's a setup task, maybe we create a sample? 
        # The task says "Validate data/manifest.csv...". If it doesn't exist, fail.
        raise FileNotFoundError(f"Required manifest file missing: {manifest_path}")

    try:
        results = ingest_pipeline(manifest_path, schema_path)
        logger.info("Ingestion and validation completed successfully.")
        # Log the DOIs of validated papers
        for pm in results:
            print(f"OK: {pm.doi}")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        # Re-raise to ensure the script exits with non-zero status on failure
        raise

if __name__ == "__main__":
    main()
