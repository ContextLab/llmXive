import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from datasets import load_dataset

from config import get_config
from utils.logging import get_logger, DataLoadError

logger = get_logger(__name__)
config = get_config()

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load existing manifest or return empty dict if not found."""
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: Dict[str, Any], manifest_path: str) -> None:
    """Save manifest to JSON file."""
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

def fetch_arxiv_pile_truncated() -> None:
    """
    Fetch the 'arXiv' subset of the Pile dataset, truncate to TOKEN_LIMIT,
    and save to data/raw/pile_arxiv_truncated.json.
    """
    logger.info("Fetching arXiv subset of The Pile...")
    try:
        dataset = load_dataset("the_pile", "pile_arxiv", split="train")
    except Exception as e:
        raise DataLoadError(f"Failed to load the_pile/pile_arxiv: {e}")

    token_limit = config.get("TOKEN_LIMIT", 100000)
    logger.info(f"Truncating to {token_limit} tokens...")

    all_text = []
    current_tokens = 0
    for item in dataset:
        text = item.get("text", "")
        # Simple token approximation: split by whitespace
        tokens = text.split()
        if current_tokens + len(tokens) > token_limit:
            remaining = token_limit - current_tokens
            if remaining <= 0:
                break
            all_text.append(" ".join(tokens[:remaining]))
            break
        all_text.append(text)
        current_tokens += len(tokens)

    truncated_text = " ".join(all_text)
    output_path = Path(config.get("DATA_DIR", "data/raw")) / "pile_arxiv_truncated.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({"text": truncated_text}, f)

    checksum = compute_checksum(str(output_path))
    manifest_path = Path(config.get("DATA_DIR", "data")) / "manifest.json"
    manifest = load_manifest(str(manifest_path))
    manifest["pile_arxiv_truncated.json"] = {
        "type": "training",
        "checksum": checksum,
        "size_bytes": output_path.stat().st_size,
        "created_at": os.popen("date -Iseconds").read().strip()
    }
    save_manifest(manifest, str(manifest_path))
    logger.info(f"Saved training data to {output_path} (checksum: {checksum})")

def fetch_gsm8k() -> None:
    """
    Fetch the GSM8K dataset from HuggingFace and save to data/raw/gsm8k.json.
    """
    logger.info("Fetching GSM8K dataset...")
    try:
        dataset = load_dataset("gsm8k", "main", split="train")
    except Exception as e:
        raise DataLoadError(f"Failed to load gsm8k: {e}")

    output_path = Path(config.get("DATA_DIR", "data/raw")) / "gsm8k.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data_list = []
    for item in dataset:
        data_list.append({
            "question": item.get("question", ""),
            "answer": item.get("answer", "")
        })

    with open(output_path, "w") as f:
        json.dump(data_list, f, indent=2)

    checksum = compute_checksum(str(output_path))
    manifest_path = Path(config.get("DATA_DIR", "data")) / "manifest.json"
    manifest = load_manifest(str(manifest_path))
    manifest["gsm8k.json"] = {
        "type": "evaluation",
        "checksum": checksum,
        "size_bytes": output_path.stat().st_size,
        "created_at": os.popen("date -Iseconds").read().strip()
    }
    save_manifest(manifest, str(manifest_path))
    logger.info(f"Saved GSM8K evaluation data to {output_path} (checksum: {checksum})")

def fetch_mmlu() -> None:
    """
    Fetch the MMLU dataset from HuggingFace and save to data/raw/mmlu.json.
    Saves the 'auxiliary_train' split as the primary evaluation set.
    """
    logger.info("Fetching MMLU dataset...")
    try:
        # MMLU is large; we fetch the auxiliary_train split which is commonly used for evaluation
        dataset = load_dataset("cais/mmlu", "all", split="auxiliary_train")
    except Exception as e:
        raise DataLoadError(f"Failed to load cais/mmlu auxiliary_train: {e}")

    output_path = Path(config.get("DATA_DIR", "data/raw")) / "mmlu.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data_list = []
    for item in dataset:
        data_list.append({
            "question": item.get("question", ""),
            "choices": item.get("choices", []),
            "subject": item.get("subject", ""),
            "answer": item.get("answer", 0)  # 0-indexed correct answer
        })

    with open(output_path, "w") as f:
        json.dump(data_list, f, indent=2)

    checksum = compute_checksum(str(output_path))
    manifest_path = Path(config.get("DATA_DIR", "data")) / "manifest.json"
    manifest = load_manifest(str(manifest_path))
    manifest["mmlu.json"] = {
        "type": "evaluation",
        "checksum": checksum,
        "size_bytes": output_path.stat().st_size,
        "created_at": os.popen("date -Iseconds").read().strip()
    }
    save_manifest(manifest, str(manifest_path))
    logger.info(f"Saved MMLU evaluation data to {output_path} (checksum: {checksum})")

def save_dataset_and_manifest() -> None:
    """
    Main entry point to fetch all datasets (training and evaluation)
    and update the manifest.
    """
    # Fetch training data
    fetch_arxiv_pile_truncated()
    # Fetch evaluation data
    fetch_gsm8k()
    fetch_mmlu()
    logger.info("All datasets fetched and manifest updated.")

def main() -> None:
    """Entry point for script execution."""
    save_dataset_and_manifest()

if __name__ == "__main__":
    main()
