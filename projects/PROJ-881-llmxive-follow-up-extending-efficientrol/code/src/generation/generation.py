import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

import yaml

from src.utils.validators import (
    validate_json_schema,
    load_and_validate_jsonl,
    TokenSequence,
    ValidityLabel,
)

# Configure logger (placeholder for actual setup logic)
logger = logging.getLogger(__name__)


class GenerationConfig:
    """Configuration for generation parameters."""
    def __init__(
        self,
        model_path: str,
        dataset_name: str,
        output_dir: str,
        batch_size: int = 50,
        temperature: float = 0.0,
    ):
        self.model_path = model_path
        self.dataset_name = dataset_name
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.temperature = temperature


def setup_logging(log_path: Optional[str] = None) -> logging.Logger:
    """Set up JSON-formatted logging."""
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logging.basicConfig(
            level=logging.INFO,
            handlers=[handler, logging.StreamHandler()],
        )
    else:
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def load_model_for_cpu_inference(model_path: str):
    """Load a small model suitable for CPU inference."""
    # Placeholder for actual model loading logic
    logger.info(f"Loading model from {model_path} for CPU inference")
    return {"model_path": model_path, "device": "cpu"}


class LayerProbabilityHook:
    """Hook to capture layer-wise probability distributions."""
    def __init__(self, layer_idx: int):
        self.layer_idx = layer_idx
        self.probabilities: Optional[List[List[float]]] = None

    def __call__(self, module, input, output):
        # Placeholder for hook logic
        pass


def capture_layer_logits(model, layer_idx: int):
    """Capture logits from a specific layer."""
    # Placeholder for actual implementation
    return None


def generate_single_pass(model, prompt: str, config: GenerationConfig) -> List[str]:
    """Generate a single sequence with temperature 0.0."""
    # Placeholder for actual generation logic
    logger.info(f"Generating single pass for prompt: {prompt[:50]}...")
    return ["token1", "token2", "token3"]


def validate_against_ground_truth(
    generated_tokens: List[str],
    ground_truth_paths: List[List[str]],
    source: str,
) -> Tuple[bool, str]:
    """
    Validate generated tokens against ground truth.
    Returns (is_valid, reason).
    """
    # Placeholder for validation logic
    # In real implementation: check against ground_truth_paths
    if generated_tokens == ground_truth_paths[0] if ground_truth_paths else []:
        return True, "matched"
    return False, "ambiguous"


def write_labeled_dataset(
    records: List[Dict[str, Any]],
    output_path: Path,
    schema_path: Path,
) -> None:
    """
    Write labeled dataset to JSONL, validating against schema.
    """
    # Load and validate schema
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    else:
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(output_path, 'w') as f:
        for record in records:
            # Validate record against schema
            validate_json_schema(record, schema)
            f.write(json.dumps(record) + '\n')
    logger.info(f"Wrote {len(records)} records to {output_path}")


def load_and_merge_outputs(
    generation_output_path: Path,
    labels_output_path: Path,
    schema_path: Path,
) -> List[Dict[str, Any]]:
    """
    Merge generation outputs with ground truth labels.
    Explicitly references dataset.schema.yaml for validation.
    """
    if not generation_output_path.exists():
        raise FileNotFoundError(f"Generation output not found: {generation_output_path}")
    if not labels_output_path.exists():
        raise FileNotFoundError(f"Labels output not found: {labels_output_path}")

    # Load generation outputs
    generation_records = load_and_validate_jsonl(generation_output_path)
    labels_records = load_and_validate_jsonl(labels_output_path)

    # Create lookup for labels by sequence_id
    labels_lookup = {r['sequence_id']: r for r in labels_records}

    merged_records = []
    for gen_rec in generation_records:
        seq_id = gen_rec['sequence_id']
        if seq_id not in labels_lookup:
            logger.warning(f"Sequence {seq_id} found in generation but not in labels. Skipping.")
            continue

        label_rec = labels_lookup[seq_id]

        # Merge records according to schema
        merged = {
            'sequence_id': seq_id,
            'tokens': gen_rec.get('tokens', []),
            'source': gen_rec.get('source', label_rec.get('source', 'unknown')),
            'validity': label_rec.get('validity', False),
            'reason': label_rec.get('reason', 'unknown'),
            'metadata': {
                'generation_id': gen_rec.get('id'),
                'label_id': label_rec.get('id'),
            },
        }
        merged_records.append(merged)

    logger.info(f"Merged {len(merged_records)} records from generation and labels.")
    return merged_records


def process_dataset(
    config: GenerationConfig,
    generation_output_path: Path,
    labels_output_path: Path,
    merged_output_path: Path,
) -> None:
    """
    Orchestrate the full pipeline: load, merge, validate, and write.
    """
    schema_path = Path("code/contracts/dataset.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Required schema not found: {schema_path}")

    logger.info("Loading and merging generation outputs with ground truth labels...")
    merged_records = load_and_merge_outputs(
        generation_output_path,
        labels_output_path,
        schema_path,
    )

    logger.info(f"Writing merged labeled dataset to {merged_output_path}...")
    write_labeled_dataset(merged_records, merged_output_path, schema_path)


def load_tokens_from_file(file_path: Path) -> List[str]:
    """Load tokens from a JSONL file."""
    return load_and_validate_jsonl(file_path)


def main():
    """Entry point for generation and merging."""
    setup_logging("code/logs/generation.log")
    config = GenerationConfig(
        model_path="code/data/models/tiny_model",
        dataset_name="gsm8k",
        output_dir="code/data/outputs",
    )

    gen_path = Path("code/data/outputs/generation.jsonl")
    labels_path = Path("code/data/outputs/labels.jsonl")
    merged_path = Path("code/data/outputs/labeled_dataset.jsonl")

    if not gen_path.exists() or not labels_path.exists():
        logger.error("Generation or labels outputs not found. Run generation first.")
        sys.exit(1)

    process_dataset(config, gen_path, labels_path, merged_path)


if __name__ == "__main__":
    main()
