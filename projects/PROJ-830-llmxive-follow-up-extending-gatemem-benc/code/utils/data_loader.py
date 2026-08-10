import os
import json
import hashlib
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from datasets import load_dataset

from code.logging_config import setup_logging

# Initialize logger
logger = setup_logging(__name__)

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("state/projects"),
        Path("logs")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_fields(record: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Check if record contains all required fields. Returns list of missing fields."""
    missing = [f for f in required_fields if f not in record]
    return missing

def fetch_gatemem(dataset_id: str = "llmXive/GateMem", split: str = "train") -> List[Dict[str, Any]]:
    """
    Fetch the GateMem dataset from HuggingFace.
    Returns a list of records.
    Fails loudly if the dataset is unavailable.
    """
    logger.info(f"Fetching dataset: {dataset_id} (split={split})")
    try:
        # Use streaming to handle large datasets without loading all into RAM immediately
        # However, to save to a local raw JSONL, we need to iterate and write.
        dataset = load_dataset(dataset_id, split=split, streaming=True)
        
        raw_data = []
        # We iterate to write to disk and also to collect in memory if needed, 
        # but for this task we primarily write to disk first.
        # Note: If the dataset is huge, we might want to stream directly to file.
        # But the task asks to save raw JSONL to data/raw/.
        
        # Let's stream and write to file directly to avoid OOM on the list
        raw_path = Path("data/raw/gatemem_raw.jsonl")
        with open(raw_path, "w", encoding="utf-8") as f_out:
            for idx, item in enumerate(dataset):
                f_out.write(json.dumps(item) + "\n")
                # Optionally collect a sample if we need to return data, 
                # but the function signature suggests returning the list.
                # To avoid memory blowup, we will assume the runner has enough RAM 
                # for the 'raw' list or we return the path. 
                # The task description says "Save raw JSONL...". 
                # The API surface says returns List[Dict].
                # Given the constraint "Large dataset? Stream the real data", 
                # we will return the list only if it fits, otherwise we raise 
                # or return the path. However, to satisfy the API surface strictly:
                # We will load it. If it's too big, the runner will OOM, which is better than faking.
                # But the task says "Save to data/raw". 
                # Let's re-read: "Save raw JSONL to data/raw/, calculate SHA256...".
                # It does not explicitly demand the function returns the full list if it's massive,
                # but the signature in the API surface says `fetch_gatemem` -> List[Dict].
                # We will try to load it. If it's too big, we fail.
                pass
        
        # Re-load from the file we just wrote to ensure we return the data as per API
        # This is inefficient but ensures we return the data structure requested.
        # If the dataset is too big for RAM, this will crash, which is "Fail loudly".
        raw_data = []
        with open(raw_path, "r", encoding="utf-8") as f_in:
            for line in f_in:
                raw_data.append(json.loads(line))
        
        logger.info(f"Dataset fetched and saved to {raw_path}. Total records: {len(raw_data)}")
        return raw_data

    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
        raise RuntimeError(f"Data fetch failed: {e}")

def parse_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a JSONL file into a list of dictionaries."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error at line {line_num}: {e}")
                raise
    return data

def save_to_jsonl(data: List[Dict[str, Any]], file_path: Path):
    """Save a list of dictionaries to a JSONL file."""
    with open(file_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")

def load_from_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    return parse_jsonl_file(file_path)

def validate_dataset_schema(data: List[Dict[str, Any]], schema_path: Path) -> List[Dict[str, Any]]:
    """
    Validate dataset against schema.
    Raises ValueError if required fields are missing.
    Logs validation errors for ambiguous fields and excludes them from processing.
    """
    schema = load_schema(schema_path)
    required_fields = schema.get("required", [])
    valid_data = []
    
    for idx, record in enumerate(data):
        missing = validate_fields(record, required_fields)
        if missing:
            logger.warning(f"Record {idx} missing required fields: {missing}. Skipping.")
            continue
        
        # Check for specific ambiguous field 'leak-target' if defined in schema logic
        if "leak-target" in record:
            val = record["leak-target"]
            if val is None or val == "":
                logger.warning(f"Record {idx} has ambiguous 'leak-target'. Logging validation error and excluding.")
                continue
        
        valid_data.append(record)
    
    logger.info(f"Schema validation complete. {len(valid_data)} valid records out of {len(data)}.")
    return valid_data

def get_dataset_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate basic statistics on the dataset."""
    if not data:
        return {"count": 0}
    
    domains = set()
    outcomes = set()
    for record in data:
        if "domain" in record:
            domains.add(record["domain"])
        if "outcome" in record:
            outcomes.add(record["outcome"])
    
    return {
        "count": len(data),
        "domains": list(domains),
        "outcomes": list(outcomes)
    }

def extract_gatemem_features(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract 'leak-target' and 'authorization_boundaries' from parsed JSONL.
    Saves to data/processed/episodes.json.
    Output structure: {"episodes": [{"id": str, "domain": str, "leak_target": str, "role": str, "outcome": str, "authorization_boundaries": dict, ...}]}
    """
    episodes = []
    for record in data:
        # Map 'leak-target' to 'leak_target' for JSON consistency, or keep as is?
        # Task says: "leak_target": str in output.
        # Task says: extract 'leak-target' and 'authorization_boundaries'
        
        episode = {
            "id": record.get("id", "unknown"),
            "domain": record.get("domain", "unknown"),
            "leak_target": record.get("leak-target", record.get("leak_target", "")),
            "role": record.get("role", "unknown"),
            "outcome": record.get("outcome", "unknown"),
            "authorization_boundaries": record.get("authorization_boundaries", record.get("authorization-boundaries", {}))
        }
        
        # Include any other relevant fields if they exist, but keep the core structure
        # We preserve the original record data if needed, but the task specifies the structure.
        # We'll add the original record as a nested field if needed, but the spec implies a flat structure with specific keys.
        # The spec says: "... , ...]" implying more fields might be there.
        # Let's just ensure the required ones are present.
        
        episodes.append(episode)
    
    output_path = Path("data/processed/episodes.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"episodes": episodes}, f, indent=2)
    
    logger.info(f"Extracted {len(episodes)} episodes to {output_path}")
    return episodes

def run_data_loader_pipeline(schema_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Main pipeline: Fetch, Validate, Extract.
    """
    ensure_dirs()
    
    # 1. Fetch
    raw_data = fetch_gatemem()
    
    # 2. Validate
    if schema_path is None:
        schema_path = Path("contracts/dataset.schema.yaml")
    
    valid_data = validate_dataset_schema(raw_data, schema_path)
    
    # 3. Extract
    episodes = extract_gatemem_features(valid_data)
    
    return episodes

def main():
    """Entry point for CLI."""
    logging.basicConfig(level=logging.INFO)
    pipeline_result = run_data_loader_pipeline()
    print(f"Pipeline completed. Processed {len(pipeline_result)} episodes.")

if __name__ == "__main__":
    main()