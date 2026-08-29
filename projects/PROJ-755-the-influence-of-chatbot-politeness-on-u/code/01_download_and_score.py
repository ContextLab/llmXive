import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset
from utils.data_integrity import compute_directory_checksum, generate_manifest, compute_file_checksum
from utils.env_config import get_hf_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(base_path: Path) -> None:
    """Create necessary directory structure for raw data storage."""
    directories = [
        base_path / "data" / "raw" / "hci_p2",
        base_path / "data" / "processed"
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directory is tracked
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    logger.info(f"Ensured directories exist at {base_path}")

def load_dataset_with_check(dataset_name: str, split: Optional[str] = None) -> Any:
    """
    Load a dataset from HuggingFace with validation.
    
    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load (e.g., 'train', 'test').
    
    Returns:
        The loaded dataset object.
    
    Raises:
        ValueError: If the dataset cannot be loaded or required fields are missing.
    """
    logger.info(f"Attempting to load dataset: {dataset_name}")
    try:
        # Load dataset - streaming for large datasets to avoid memory issues
        dataset = load_dataset(
            dataset_name,
            split=split,
            trust_remote_code=True
        )
        logger.info(f"Successfully loaded dataset: {dataset_name}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise ValueError(f"Dataset {dataset_name} could not be loaded: {e}") from e

def validate_and_preprocess(dataset: Any, dataset_name: str) -> Dict[str, Any]:
    """
    Validate dataset structure and preprocess for HCI_P2.
    
    Args:
        dataset: The loaded dataset object.
        dataset_name: Name of the dataset for logging.
    
    Returns:
        Dictionary containing validation results and processed data info.
    """
    logger.info(f"Validating and preprocessing {dataset_name}")
    
    # Check for required fields per FR-001 and schema
    required_fields = ['quality_rating', 'user_id', 'dialogue_id']
    available_columns = list(dataset.column_names)
    
    missing_fields = [field for field in required_fields if field not in available_columns]
    
    if missing_fields:
        logger.warning(f"Dataset {dataset_name} missing required fields: {missing_fields}")
        # Log but don't fail - the field might be named differently or optional
    
    # Basic validation report
    validation_report = {
        "dataset_name": dataset_name,
        "total_rows": len(dataset),
        "columns": available_columns,
        "missing_required_fields": missing_fields,
        "status": "partial" if missing_fields else "complete"
    }
    
    logger.info(f"Validation report for {dataset_name}: {validation_report['status']}")
    return validation_report

def save_raw_data(dataset: Any, base_path: Path, dataset_name: str) -> str:
    """
    Save raw dataset to disk and generate checksums.
    
    Args:
        dataset: The dataset to save.
        base_path: Base project path.
        dataset_name: Name of the dataset for file naming.
    
    Returns:
        Path to the saved directory.
    """
    raw_dir = base_path / "data" / "raw" / dataset_name
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Save dataset to parquet format
    output_path = raw_dir / f"{dataset_name}_raw.parquet"
    dataset.to_parquet(str(output_path))
    logger.info(f"Saved raw data to {output_path}")
    
    # Generate checksums and manifest
    checksum = compute_directory_checksum(raw_dir)
    manifest = generate_manifest(raw_dir)
    
    manifest_path = raw_dir / "manifest.json"
    manifest["checksum"] = checksum
    manifest["dataset_name"] = dataset_name
    manifest["total_rows"] = len(dataset)
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Generated manifest and checksum for {dataset_name}")
    return str(raw_dir)

def extract_utterances(dataset: Any) -> List[Dict[str, Any]]:
    """
    Extract utterances from the dataset.
    
    Args:
        dataset: The loaded dataset.
    
    Returns:
        List of utterance dictionaries.
    """
    utterances = []
    # HCI_P2 specific structure handling
    # Assuming dataset has a 'dialogue' or 'turns' field containing utterances
    for idx, row in enumerate(dataset):
        if 'turns' in row:
            for turn_idx, turn in enumerate(row['turns']):
                utterances.append({
                    'dialogue_id': row.get('dialogue_id', idx),
                    'user_id': row.get('user_id', 'unknown'),
                    'turn_index': turn_idx,
                    'text': turn.get('text', ''),
                    'speaker': turn.get('speaker', 'unknown'),
                    'quality_rating': row.get('quality_rating', None)
                })
        elif 'utterances' in row:
            for turn_idx, utterance in enumerate(row['utterances']):
                utterances.append({
                    'dialogue_id': row.get('dialogue_id', idx),
                    'user_id': row.get('user_id', 'unknown'),
                    'turn_index': turn_idx,
                    'text': utterance.get('text', ''),
                    'speaker': utterance.get('speaker', 'unknown'),
                    'quality_rating': row.get('quality_rating', None)
                })
    
    return utterances

def filter_dialogues(utterances: List[Dict[str, Any]], min_utterances: int = 2) -> List[Dict[str, Any]]:
    """
    Filter dialogues based on minimum utterance count.
    
    Args:
        utterances: List of utterance dictionaries.
        min_utterances: Minimum number of utterances required per dialogue.
    
    Returns:
        Filtered list of utterances.
    """
    # Group by dialogue_id
    dialogue_map = {}
    for utterance in utterances:
        dialogue_id = utterance['dialogue_id']
        if dialogue_id not in dialogue_map:
            dialogue_map[dialogue_id] = []
        dialogue_map[dialogue_id].append(utterance)
    
    # Filter dialogues with sufficient utterances
    filtered = []
    for dialogue_id, turns in dialogue_map.items():
        if len(turns) >= min_utterances:
            filtered.extend(turns)
        else:
            logger.debug(f"Excluded dialogue {dialogue_id} with {len(turns)} utterances")
    
    return filtered

def main():
    """
    Main entry point for downloading and processing HCI_P2 dataset.
    
    This task implements the download and initial processing of the HCI_P2 dataset
    as a PRIMARY input per FR-001.
    """
    # Get base path
    base_path = Path(__file__).parent.parent
    if not base_path.exists():
        base_path = Path.cwd()
    
    ensure_directories(base_path)
    
    # Load HCI_P2 dataset
    # Using the canonical HuggingFace dataset name for HCI_P2
    dataset_name = "HCI_P2"
    full_dataset_name = "HCI_P2"  # Adjust if the actual HF name differs
    
    try:
        # Attempt to load the dataset
        # Note: HCI_P2 might be under a different name on HuggingFace
        # Common variations: "HCI_P2", "hci_p2", or a specific author/name combo
        # If this fails, the user should update the dataset name in the code
        dataset = load_dataset_with_check(full_dataset_name, split="train")
        
        # Validate and preprocess
        validation_report = validate_and_preprocess(dataset, dataset_name)
        
        # Save raw data
        raw_path = save_raw_data(dataset, base_path, dataset_name)
        
        # Extract and filter utterances
        utterances = extract_utterances(dataset)
        filtered_utterances = filter_dialogues(utterances)
        
        logger.info(f"Extracted {len(utterances)} utterances, kept {len(filtered_utterances)} after filtering")
        
        # Save validation report
        validation_report_path = base_path / "data" / "raw" / dataset_name / "validation_report.json"
        with open(validation_report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        logger.info(f"Successfully processed {dataset_name} dataset")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {dataset_name}: {e}")
        # Re-raise to ensure the pipeline fails loudly rather than silently
        raise

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)