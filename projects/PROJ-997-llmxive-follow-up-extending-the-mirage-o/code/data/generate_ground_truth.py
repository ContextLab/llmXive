"""
Wrapper script for the quick‑start command.

The original quick‑start invokes
    python code/data/generate_ground_truth.py --model ... --levels INT4 INT8 FP8 --output ...

The core implementation lives in ``code/cli/generate_ground_truth.py`` where the
heavy‑lifting functions are defined.  This thin wrapper adapts the quick‑start
arguments to the core implementation, supplies a default location for the
JSON statistics file (``data/processed/dataset_stats.json``), and forwards the
call.

The script writes two artefacts:
  * ``data/processed/training_sample.parquet`` – the dataset described in T015.
  * ``data/processed/dataset_stats.json``   – statistical summary required by
    the verification step.
"""

import argparse
from pathlib import Path
import sys

# Import the core functions so we can reuse the implementation without
# duplicating code.  The core module lives in ``code/cli``.
sys.path.append(str(Path(__file__).resolve().parents[2] / "code" / "cli"))
from generate_ground_truth import (
    load_full_precision_model,
    quantize_model_int8,
    quantize_model_fp16,
    compute_kl,
    get_logits,
    compute_gradient_norm,
    download_gsm8k_subset,
)

import logging
logging.basicConfig(level=logging.INFO)

def run_wrapper(model: str, levels: list, output_path: str, sample_size: int = 300):
    """
    Execute the ground‑truth generation pipeline using the core functions.
    """
    # Resolve paths
    parquet_path = Path(output_path).expanduser().resolve()
    stats_path = Path("data/processed/dataset_stats.json").expanduser().resolve()

    # ------------------------------------------------------------------- #
    # 1. Load data
    # ------------------------------------------------------------------- #
    subset = download_gsm8k_subset(sample_size)

    # ------------------------------------------------------------------- #
    # 2. Load models
    # ------------------------------------------------------------------- #
    full_model, tokenizer = load_full_precision_model(model)

    # ------------------------------------------------------------------- #
    # 3. Prepare quantized variants (same mapping as the core script)
    # ------------------------------------------------------------------- #
    quantized_models = {}
    for level in levels:
        if level == "INT8":
            quantized_models["INT8"] = quantize_model_int8(full_model)
        elif level == "FP8":
            quantized_models["FP8"] = quantize_model_fp16(full_model)
        elif level == "INT4":
            # Proxy using INT8 as INT4 is not natively supported
            quantized_models["INT4"] = quantize_model_int8(full_model)
        else:
            raise ValueError(f"Unsupported quantization level: {level}")

    # ------------------------------------------------------------------- #
    # 4. Process each sample
    # ------------------------------------------------------------------- #
    import pandas as pd
    import numpy as np
    import torch.nn.functional as F
    from tqdm.auto import tqdm

    records = []
    for idx, sample in tqdm(enumerate(subset), total=len(subset)):
        prompt = sample["question"]
        target = sample["answer"].split("\n")[0]

        full_logits = get_logits(full_model, tokenizer, prompt)
        full_probs = F.softmax(full_logits, dim=-1).cpu().numpy()

        grad_norm = compute_gradient_norm(full_model, tokenizer, prompt, target)
        curvature = grad_norm ** 2

        for level, q_model in quantized_models.items():
            q_logits = get_logits(q_model, tokenizer, prompt)
            q_probs = F.softmax(q_logits, dim=-1).cpu().numpy()
            kl = compute_kl(full_probs, q_probs)

            records.append(
                {
                    "input_id": idx,
                    "quantization_level": level,
                    "gradient_norm": grad_norm,
                    "local_curvature": curvature,
                    "kl_divergence": kl,
                }
            )

    df = pd.DataFrame.from_records(records)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False)

    # ------------------------------------------------------------------- #
    # 5. Compute statistics (same as core script)
    # ------------------------------------------------------------------- #
    stats = {}
    for level in levels:
        level_kl = df[df["quantization_level"] == level]["kl_divergence"].values
        from scipy.stats import ttest_1samp
        t_stat, p_val = ttest_1samp(level_kl, popmean=0.0)
        stats[level] = {
            "sample_count": int(len(level_kl)),
            "mean_kl": float(np.mean(level_kl)),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "non_zero_fraction": float(np.mean(level_kl > 0)),
        }

    overall_significant = any(v["p_value"] < 0.05 for v in stats.values())
    summary = {
        "per_level_statistics": stats,
        "overall_non_zero_kl_significant": overall_significant,
    }

    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        import json
        json.dump(summary, f, indent=2)

    logging.info("Wrapper completed successfully.")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quick‑start wrapper for T015 – generate ground truth data."
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Hugging‑Face model identifier (e.g., meta-llama/Meta-Llama-3-8B).",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        required=True,
        help="Quantization levels (e.g., INT4 INT8 FP8).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for the Parquet dataset output.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="Number of GSM8K samples to process (default 300).",
    )
    args = parser.parse_args()
    run_wrapper(
        model=args.model,
        levels=args.levels,
        output_path=args.output,
        sample_size=args.sample_size,
    )

if __name__ == "__main__":
    main()
