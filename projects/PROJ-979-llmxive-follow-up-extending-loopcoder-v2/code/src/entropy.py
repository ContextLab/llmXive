"""
Entropy extraction module for llmXive.
Handles entropy calculation from model samples with robust error handling.
"""
import ast
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
import numpy as np
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.config import get_config_value
from src.utils import set_global_seed

# Configure module‑level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def load_model(
    model_name: str,
    device: str = "cuda",
    temperature: float = 0.7,
    top_p: float = 0.95,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load a causal language model and its tokenizer.
    """
    logger.info(f"Loading model {model_name} on {device}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )
    if device == "cpu":
        model = model.to(torch.float32)
    model.eval()
    logger.info("Model loaded successfully")
    return model, tokenizer


def normalize_ast(code_str: str) -> Optional[str]:
    """Normalise a piece of Python code by parsing it to an AST and unparsing it."""
    try:
        tree = ast.parse(code_str)
        return ast.unparse(tree)
    except Exception:
        logger.debug("Failed to parse code for AST normalisation")
        return None


def generate_samples(
    model,
    tokenizer,
    prompt: str,
    n_samples: int = 10,
    temperature: float = 0.7,
    top_p: float = 0.95,
    max_new_tokens: int = 512,
) -> List[str]:
    """Generate ``n_samples`` completions for ``prompt``."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    samples: List[str] = []

    for _ in range(n_samples):
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if prompt in generated:
            generated = generated.split(prompt, 1)[1]
        samples.append(generated.strip())
    return samples


def cluster_samples(samples: List[str]) -> Dict[str, int]:
    """Cluster generated samples by the hash of their normalised AST."""
    clusters: Dict[str, int] = {}
    for sample in samples:
        norm = normalize_ast(sample)
        if norm is None:
            continue
        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        clusters[h] = clusters.get(h, 0) + 1
    return clusters


def compute_shannon_entropy(cluster_counts: Dict[str, int]) -> float:
    """Compute Shannon entropy (base‑2) from a dictionary of cluster counts."""
    total = sum(cluster_counts.values())
    if total == 0:
        return 1e-9  # minimal non‑zero entropy
    entropy = 0.0
    for count in cluster_counts.values():
        p = count / total
        entropy -= p * np.log2(p)
    return float(entropy)


def load_reference_set(path: str) -> pd.DataFrame:
    """Load an optional reference validation set (used only for sanity checks)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Reference set not found at {path}")
    return pd.read_csv(path)


def process_entropy_for_dataset(
    dataset_path: str,
    output_path: str,
    reference_path: Optional[str],
    model_name: str,
    device: str = "cuda",
    n_samples: int = 10,
    seed: int = 42,
    sample_size: Optional[int] = None,
) -> None:
    """
    Compute entropy for every problem in ``dataset_path`` and write a CSV.
    """
    set_global_seed(seed)

    temperature = float(get_config_value("MODEL_TEMP", 0.7))
    top_p = float(get_config_value("MODEL_TOP_P", 0.95))

    model, tokenizer = load_model(
        model_name, device=device, temperature=temperature, top_p=top_p
    )

    # Load dataset (JSON or CSV)
    if dataset_path.endswith(".json"):
        with open(dataset_path, "r") as f:
            data = json.load(f)
    elif dataset_path.endswith(".csv"):
        data = pd.read_csv(dataset_path).to_dict("records")
    else:
        raise ValueError(f"Unsupported dataset format: {dataset_path}")

    if sample_size is not None:
        data = data[:sample_size]

    # Optional reference set (only for logging)
    if reference_path and os.path.exists(reference_path):
        try:
            _ = load_reference_set(reference_path)
            logger.info("Reference set loaded for sanity checking")
        except Exception as e:
            logger.warning(f"Could not load reference set: {e}")

    results: List[Dict[str, Any]] = []
    exclusion_log: List[Dict[str, Any]] = []

    for idx, problem in enumerate(data):
        task_id = problem.get("task_id", f"unknown_{idx}")
        prompt = problem.get("prompt", "")

        if not prompt:
            exclusion_log.append(
                {
                    "task_id": task_id,
                    "reason": "Empty prompt",
                    "error": "No prompt provided",
                }
            )
            continue

        try:
            samples = generate_samples(
                model,
                tokenizer,
                prompt,
                n_samples=n_samples,
                temperature=temperature,
                top_p=top_p,
            )
            valid_samples = [s for s in samples if s.strip()]
            if not valid_samples:
                exclusion_log.append(
                    {
                        "task_id": task_id,
                        "reason": "No valid samples generated",
                        "error": "All samples were empty strings",
                    }
                )
                continue

            clusters = cluster_samples(valid_samples)
            if not clusters:
                exclusion_log.append(
                    {
                        "task_id": task_id,
                        "reason": "All samples malformed",
                        "error": "AST parsing failed for every sample",
                    }
                )
                results.append(
                    {"task_id": task_id, "entropy": 1e-9, "exclusion_reason": "all_samples_malformed"}
                )
                continue

            entropy = compute_shannon_entropy(clusters)
            results.append({"task_id": task_id, "entropy": entropy, "exclusion_reason": None})
        except Exception as exc:
            err_msg = str(exc)
            exclusion_log.append(
                {"task_id": task_id, "reason": "Processing error", "error": err_msg}
            )
            logger.error(f"Error processing {task_id}: {err_msg}")
            results.append(
                {"task_id": task_id, "entropy": 1e-9, "exclusion_reason": f"processing_error: {err_msg[:100]}"}
            )

        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(data)} problems")

    # Write main CSV
    out_df = pd.DataFrame(results)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_path, index=False)
    logger.info(f"Entropy results written to {output_path}")

    # Write exclusion log
    exclusion_path = Path(output_path).with_name("exclusion_log.json")
    with open(exclusion_path, "w") as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log written to {exclusion_path}")


def main() -> None:
    """CLI entry point with sensible defaults."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute entropy for a set of code generation problems"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(Path(get_config_value("DATA_DIR", "data")) / "processed" / "filtered_splits.json"),
        help="Path to input dataset",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(get_config_value("OUTPUT_DIR", "data/processed") ) / "entropy_results.csv"),
        help="Destination CSV",
    )
    parser.add_argument(
        "--reference",
        type=str,
        default=None,
        help="Optional reference validation set (unused in entropy calculation)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=get_config_value("MODEL_NAME"),
        help="HuggingFace model identifier",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cpu", "cuda"],
        help="Execution device",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=int(get_config_value("ENTROPY_N_SAMPLES", 10)),
        help="Samples per problem",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(get_config_value("RANDOM_SEED", 42)),
        help="Random seed",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Process only the first N problems (for quick runs)",
    )

    args = parser.parse_args()

    process_entropy_for_dataset(
        dataset_path=args.input,
        output_path=args.output,
        reference_path=args.reference,
        model_name=args.model,
        device=args.device,
        n_samples=args.n_samples,
        seed=args.seed,
        sample_size=args.sample_size,
    )


if __name__ == "__main__":
    main()
