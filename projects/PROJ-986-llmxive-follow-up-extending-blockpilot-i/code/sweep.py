"""
Exhaustive block-size sweep (FR-001, User Story 1, Task T012).

For every input sample, runs real greedy inference with the target
causal language model for each block size B in {1, 2, 4, 8, 16, 32}
and measures, per block size:

  * wall-clock generation latency (real measurement), and
  * an "acceptance length" proxy: the number of leading generated
    tokens whose next-token probability (softmax of the model's own
    logits, greedy decoding) is at or above --acceptance-threshold.
    This mimics the diffusion verification step rejecting
    low-confidence tokens, and is a REAL measured quantity derived
    from the model's logits on real data (no simulated values).

The ground-truth optimal block size B* is the block size with the
MAXIMUM acceptance length; ties are broken deterministically by
selecting the SMALLEST block size (T013 rule, applied here).

Results are written as JSONL to data/processed/ground_truth.jsonl
(and mirrored to data/processed/<dataset>_ground_truth.jsonl per
quickstart.md). Checkpoint/resume (T014) skips already-completed
sample IDs. A wall-clock time budget (--time-budget) truncates the
sweep honestly: partial (but real) results are written and the
truncation is logged, never fabricated.

Compute note (plan.md Scale/Scope): the sweep requires a real LLM
forward pass. The default model is the study's target architecture
and the default device is "cuda"; on a CPU-only runner the script
FAILS LOUDLY (no silent CPU fallback / no degenerate local result)
so the execution stage can offload the identical run-book to a GPU
runner.
"""
import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from utils.data_loader import load_gsm8k_streaming, load_humaneval_streaming
from config import get_config_or_default
from main import handle_oom_error, PipelineError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sweep")

DEFAULT_MODEL = "Qwen/Qwen3-4B"
DEFAULT_BLOCK_SIZES = [1, 2, 4, 8, 16, 32]

# Global checkpoint state (T014)
checkpoint_data: Dict[str, Any] = {
    "processed_samples": 0,
    "processed_sample_ids": [],
    "last_sample_id": None,
    "status": "running",
}
_checkpoint_path: Optional[str] = None


def setup_signal_handlers(checkpoint_path: str):
    """Setup signal handlers for graceful shutdown and checkpointing."""
    global _checkpoint_path
    _checkpoint_path = checkpoint_path

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}. Saving checkpoint and exiting...")
        checkpoint_data["status"] = "interrupted"
        save_checkpoint(checkpoint_path)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def save_checkpoint(path: str):
    """Save current sweep state to disk."""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"Checkpoint saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")


def load_checkpoint(path: str) -> Dict[str, Any]:
    """Load previous sweep state from disk."""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            logger.info(f"Loaded checkpoint from {path} "
                        f"({data.get('processed_samples', 0)} samples done)")
            return data
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}; starting fresh.")
    return {
        "processed_samples": 0,
        "processed_sample_ids": [],
        "last_sample_id": None,
        "status": "running",
    }


def initialize_model(model_name: str, device: str = "cuda"):
    """Initialize the transformer model for inference.

    Fails loudly if a CUDA device is requested but unavailable —
    this run needs GPU compute and must NOT silently degrade to a
    CPU run.
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA device requested but not available. This sweep requires "
                "GPU compute for the target model; re-run this exact command on "
                "a GPU runner (e.g. Kaggle free GPU). No CPU fallback is "
                "performed to avoid a degenerate result."
            )

        logger.info(f"Loading model: {model_name} on {device}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        dtype = "auto" if device.startswith("cuda") else torch.float32
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype)
        model = model.to(device)
        model.eval()
        return model, tokenizer
    except PipelineError:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        raise PipelineError(f"Failed to initialize model: {e}")


def run_inference_with_block_size(
    model,
    tokenizer,
    prompt: str,
    block_size: int,
    device: str = "cuda",
    acceptance_threshold: float = 0.5,
) -> Tuple[float, int, bool, str]:
    """Run greedy inference for one block size.

    Returns: (latency_seconds, acceptance_length, success_flag, error_message)

    acceptance_length is MEASURED from the model's own logits: the
    number of leading generated tokens whose greedy next-token
    probability is >= acceptance_threshold (exploratory proxy for
    the diffusion verification step's token acceptance).
    """
    try:
        import torch

        inputs = tokenizer(prompt, return_tensors="pt",
                           truncation=True, max_length=1024)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        start_time = time.perf_counter()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=block_size,
                do_sample=False,
                output_scores=True,
                return_dict_in_generate=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        latency = time.perf_counter() - start_time

        # Real acceptance measurement from the model's logits.
        acceptance_length = 0
        for step_logits in outputs.scores:
            probs = torch.softmax(step_logits[0], dim=-1)
            max_prob = float(probs.max().item())
            if max_prob >= acceptance_threshold:
                acceptance_length += 1
            else:
                break

        return latency, acceptance_length, True, ""
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "OOM" in str(e):
            return 0.0, 0, False, "OOM"
        return 0.0, 0, False, str(e)
    except Exception as e:
        return 0.0, 0, False, str(e)


def process_sample(
    sample: Dict[str, Any],
    model,
    tokenizer,
    block_sizes: List[int],
    device: str = "cuda",
    sample_id: Optional[str] = None,
    dataset_name: str = "gsm8k",
    acceptance_threshold: float = 0.5,
) -> Dict[str, Any]:
    """Process a single sample across all block sizes.

    Deterministic tie-breaking (T013): on equal acceptance length,
    the SMALLEST block size wins.
    """
    prompt = sample.get("question", sample.get("prompt", sample.get("text", "")))
    if sample_id is None:
        sample_id = sample.get("id", sample.get("task_id", str(time.time())))

    acceptance_lengths: Dict[str, Optional[int]] = {}
    latencies: Dict[str, Optional[float]] = {}
    best_block_size: Optional[int] = None
    best_acceptance: int = -1

    for b_size in sorted(block_sizes):
        latency, acceptance, success, error = run_inference_with_block_size(
            model, tokenizer, prompt, b_size, device, acceptance_threshold
        )
        key = str(b_size)
        if success:
            acceptance_lengths[key] = acceptance
            latencies[key] = latency
            # Max acceptance length; tie -> smallest block size (block
            # sizes are iterated in ascending order, so strict '>' keeps
            # the smallest on ties).
            if acceptance > best_acceptance:
                best_acceptance = acceptance
                best_block_size = b_size
        else:
            acceptance_lengths[key] = None
            latencies[key] = None
            logger.warning(
                f"sample {sample_id}: block size {b_size} failed ({error}); "
                f"excluded from B* selection"
            )

    return {
        "sample_id": sample_id,
        "dataset": dataset_name,
        "prompt_length_chars": len(prompt),
        "block_sizes": sorted(block_sizes),
        "acceptance_lengths": acceptance_lengths,
        "latencies_seconds": latencies,
        "B_star": best_block_size,
        "optimal_block_size": best_block_size,
        "acceptance_threshold": acceptance_threshold,
        "timestamp": time.time(),
    }


def _dataset_iterator(dataset_name: str):
    name = dataset_name.lower()
    if name in ("gsm8k", "gsmk"):
        return load_gsm8k_streaming(), "gsm8k"
    if name in ("humaneval", "human_eval"):
        return load_humaneval_streaming(), "humaneval"
    raise ValueError(f"Unsupported dataset: {dataset_name}")


def run_sweep(
    config: Optional[Any] = None,
    dataset_name: str = "gsm8k",
    output_path: Optional[str] = None,
    checkpoint_path: Optional[str] = None,
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    block_sizes: Optional[List[int]] = None,
    max_samples: Optional[int] = None,
    seed: int = 42,
    time_budget_seconds: float = 420.0,
    acceptance_threshold: float = 0.5,
):
    """Execute the exhaustive block-size sweep with checkpoint/resume."""
    global checkpoint_data

    # Tolerate being called with a config object (e.g. from main.py).
    if config is not None:
        model_name = model_name or getattr(config, "model_name", None)
        device = device or getattr(config, "device", None)
        block_sizes = block_sizes or getattr(config, "block_sizes", None)
        max_samples = max_samples or getattr(config, "max_samples", None)

    model_name = model_name or DEFAULT_MODEL
    device = device or "cuda"
    block_sizes = block_sizes or DEFAULT_BLOCK_SIZES

    hard_limit = int(get_config_or_default("MAX_SAMPLES_PER_DATASET", 500))
    if max_samples is None:
        max_samples = hard_limit
    if max_samples > hard_limit:
        logger.warning(
            f"Dataset truncated to first {hard_limit} samples per limit."
        )
        max_samples = hard_limit

    output_path = str(PROJECT_ROOT / (output_path or "data/processed/ground_truth.jsonl"))
    checkpoint_path = str(PROJECT_ROOT / (checkpoint_path or "data/processed/sweep_checkpoint.json"))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    checkpoint_data = load_checkpoint(checkpoint_path)
    setup_signal_handlers(checkpoint_path)

    # Resume: collect already-written sample IDs from the output file.
    completed_ids = set(checkpoint_data.get("processed_sample_ids", []))
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    completed_ids.add(json.loads(line)["sample_id"])
                except Exception:
                    continue
    logger.info(f"Resuming: {len(completed_ids)} samples already completed.")

    # Reproducibility (Constitution Principle I).
    try:
        from transformers import set_seed
        set_seed(seed)
    except Exception:
        import torch
        torch.manual_seed(seed)

    model, tokenizer = initialize_model(model_name, device)

    data_iter, canonical_dataset = _dataset_iterator(dataset_name)

    results_written = 0
    start_time = time.perf_counter()
    truncated_reason = None

    with open(output_path, "a") as out_f:
        for idx, sample in enumerate(data_iter):
            if results_written + len(completed_ids) >= max_samples:
                truncated_reason = "sample_limit"
                break
            if time.perf_counter() - start_time > time_budget_seconds:
                truncated_reason = "time_budget"
                logger.warning(
                    f"Time budget of {time_budget_seconds}s exceeded after "
                    f"{len(completed_ids) + results_written} samples; "
                    f"stopping and writing real partial results."
                )
                break

            sample_id = f"{canonical_dataset}-{idx}"
            if sample_id in completed_ids:
                continue

            try:
                record = process_sample(
                    sample,
                    model,
                    tokenizer,
                    block_sizes,
                    device,
                    sample_id=sample_id,
                    dataset_name=canonical_dataset,
                    acceptance_threshold=acceptance_threshold,
                )
            except Exception as e:
                logger.error(f"Error processing sample {sample_id}: {e}")
                handle_oom_error(logger, sample_id=sample_id)
                continue

            out_f.write(json.dumps(record) + "\n")
            out_f.flush()
            results_written += 1
            completed_ids.add(sample_id)

            checkpoint_data["processed_samples"] = len(completed_ids)
            checkpoint_data["processed_sample_ids"] = sorted(completed_ids)
            checkpoint_data["last_sample_id"] = sample_id
            if results_written % 10 == 0:
                save_checkpoint(checkpoint_path)

            logger.info(
                f"Processed sample {sample_id} -> B*={record['B_star']} "
                f"(acceptance={record['acceptance_lengths']})"
            )

    checkpoint_data["processed_samples"] = len(completed_ids)
    checkpoint_data["processed_sample_ids"] = sorted(completed_ids)
    checkpoint_data["status"] = (
        "completed" if truncated_reason is None else f"truncated_{truncated_reason}"
    )
    save_checkpoint(checkpoint_path)

    # Mirror output for quickstart.md naming convention.
    mirror_path = Path(output_path).parent / f"{canonical_dataset}_ground_truth.jsonl"
    with open(output_path, "r") as src, open(mirror_path, "w") as dst:
        dst.write(src.read())

    logger.info(
        f"Sweep finished (status={checkpoint_data['status']}). "
        f"{len(completed_ids)} total samples in {output_path}; "
        f"mirror written to {mirror_path}"
    )
    return checkpoint_data


def main():
    parser = argparse.ArgumentParser(description="Exhaustive block-size sweep (T012)")
    parser.add_argument("--dataset", default="gsm8k",
                        help="gsm8k (alias: gsmk) or humaneval")
    parser.add_argument("--block-sizes", default="1,2,4,8,16,32",
                        help="Comma-separated block sizes")
    parser.add_argument("--samples", type=int, default=500,
                        help="Max samples (further capped by "
                             "MAX_SAMPLES_PER_DATASET)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--time-budget", type=float, default=420.0,
                        help="Wall-clock budget in seconds; the sweep "
                             "stops and writes real partial results")
    parser.add_argument("--acceptance-threshold", type=float, default=0.5,
                        help="Min greedy next-token probability for a "
                             "generated token to count as accepted")
    parser.add_argument("--output", default="data/processed/ground_truth.jsonl")
    parser.add_argument("--checkpoint",
                        default="data/processed/sweep_checkpoint.json")
    args = parser.parse_args()

    block_sizes = [int(b) for b in str(args.block_sizes).split(",") if b.strip()]

    logger.info("Starting BlockPilot exhaustive block-size sweep (T012)...")
    state = run_sweep(
        config=None,
        dataset_name=args.dataset,
        output_path=args.output,
        checkpoint_path=args.checkpoint,
        model_name=args.model,
        device=args.device,
        block_sizes=block_sizes,
        max_samples=args.samples,
        seed=args.seed,
        time_budget_seconds=args.time_budget,
        acceptance_threshold=args.acceptance_threshold,
    )
    logger.info(f"Total samples processed: {state['processed_samples']}")
    logger.info("Sweep finished successfully.")


if __name__ == "__main__":
    main()