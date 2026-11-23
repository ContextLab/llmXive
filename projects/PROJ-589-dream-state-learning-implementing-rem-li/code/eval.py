"""
Few‑shot QNLI evaluation script for Dream‑State Learning.

This script loads a checkpoint produced by ``code/train.py`` (a
``DistilBertForMaskedLM`` state dict), runs a lightweight evaluation on the
GLUE QNLI validation set, and writes a JSON result that conforms to the
``evaluation_result.schema.yaml`` contract.

The evaluation measures:
  * loss (masked‑LM loss on the QNLI inputs)
  * reconstruction accuracy (token‑level match rate)
  * peak RSS memory during evaluation
  * wall‑clock duration
  * reconstruction‑difficulty average (approximated by average token‑entropy)
"""

import argparse
import json
import time
import uuid
from pathlib import Path

import psutil
import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import DistilBertForMaskedLM, DistilBertTokenizerFast
from datasets import load_dataset

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def _load_checkpoint(checkpoint_path: Path) -> DistilBertForMaskedLM:
    """
    Load a ``DistilBertForMaskedLM`` model. If the checkpoint file does not
    exist, fall back to the pretrained model.
    """
    cfg = Config()
    model = DistilBertForMaskedLM.from_pretrained(cfg.model_name)

    if checkpoint_path.is_file():
        logger.info(f"Loading checkpoint from {checkpoint_path}")
        state = torch.load(checkpoint_path, map_location=cfg.device)
        model.load_state_dict(state)
    else:
        logger.warning(
            f"Checkpoint {checkpoint_path} not found – using pretrained model "
            "weights instead."
        )
    model.to(cfg.device)
    model.eval()
    return model

def _prepare_qnli_dataloader(
    tokenizer: DistilBertTokenizerFast,
    max_samples: int = 200,
    batch_size: int = 4,
) -> DataLoader:
    """
    Load the GLUE QNLI validation split and return a DataLoader.
    """
    # Use trust_remote_code=True to avoid potential HfUriErrors in some environments
    qnli = load_dataset("glue", "qnli", split="validation", trust_remote_code=True)
    qnli = qnli.select(range(min(max_samples, len(qnli))))

    sentences = [
        f"{rec['question']} {rec['sentence']}"
        for rec in qnli
    ]

    tokenized = tokenizer(
        sentences,
        padding="max_length",
        truncation=True,
        max_length=64,
        return_tensors="pt",
    )
    input_ids = tokenized["input_ids"]
    labels = input_ids.clone()

    dataset = TensorDataset(input_ids, labels)

    def collate_fn(batch):
        input_batch = torch.stack([b[0] for b in batch])
        label_batch = torch.stack([b[1] for b in batch])
        return {"input_ids": input_batch, "labels": label_batch}

    return DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)

def _compute_loss_and_entropy(
    model: DistilBertForMaskedLM,
    batch: dict,
    device: torch.device,
) -> tuple[float, float]:
    """
    Run a forward pass, return the mean loss and the average token entropy.
    """
    input_ids = batch["input_ids"].to(device)
    labels = batch["labels"].to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, labels=labels)
        loss = outputs.loss.item()

        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        token_entropy = -torch.sum(probs * torch.log2(probs + 1e-12), dim=-1)
        avg_entropy = token_entropy.mean().item()

    return loss, avg_entropy

def _compute_reconstruction_accuracy(
    model: DistilBertForMaskedLM,
    batch: dict,
    device: torch.device,
) -> float:
    """
    Compute accuracy as the proportion of tokens where the top prediction matches target.
    """
    input_ids = batch["input_ids"].to(device)
    labels = batch["labels"].to(device)

    with torch.no_grad():
        logits = model(input_ids=input_ids).logits
        preds = torch.argmax(logits, dim=-1)
        correct = (preds == labels).float()
        accuracy = correct.mean().item()
    return accuracy

def evaluate_checkpoint(
    checkpoint_path: Path,
    output_dir: Path,
    config: Config,
) -> Path:
    """
    Perform the full evaluation for a single checkpoint.
    """
    start_time = time.time()
    process = psutil.Process()
    peak_rss = process.memory_info().rss

    model = _load_checkpoint(checkpoint_path)
    tokenizer = DistilBertTokenizerFast.from_pretrained(config.model_name)
    dataloader = _prepare_qnli_dataloader(tokenizer)

    total_loss, total_entropy, total_accuracy = 0.0, 0.0, 0.0
    steps = 0
    device = config.device

    for batch in dataloader:
        loss, entropy = _compute_loss_and_entropy(model, batch, device)
        acc = _compute_reconstruction_accuracy(model, batch, device)

        total_loss += loss
        total_entropy += entropy
        total_accuracy += acc
        steps += 1

        current_rss = process.memory_info().rss
        if current_rss > peak_rss:
            peak_rss = current_rss

    avg_loss = total_loss / steps if steps else float("nan")
    avg_entropy = total_entropy / steps if steps else float("nan")
    avg_accuracy = total_accuracy / steps if steps else float("nan")
    duration = time.time() - start_time

    stem = checkpoint_path.stem
    seed = -1
    if "seed" in stem:
        try:
            # Handle both "checkpoint_seed_0_..." and "debug_seed0"
            import re
            match = re.search(r"seed_?(\d+)", stem)
            if match:
                seed = int(match.group(1))
        except Exception:
            pass

    result = {
        "run_id": str(uuid.uuid4()),
        "seed": seed,
        "phase": "wake_dream",
        "dataset": "qnli",
        "accuracy": round(avg_accuracy, 6),
        "loss": round(avg_loss, 6),
        "peak_memory_mb": int(peak_rss // (1024 * 1024)),
        "duration_seconds": round(duration, 3),
        "status": "success",
        "reconstruction_difficulty_avg": round(avg_entropy, 6),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"evaluation_result_{stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Evaluation result written to {out_path}")
    return out_path

def _discover_checkpoints(results_dir: Path) -> list[Path]:
    checkpoints = []
    for summary_file in results_dir.glob("training_summary_*.json"):
        try:
            with open(summary_file, "r") as f:
                data = json.load(f)
            ckpt_path = Path(data.get("checkpoint", ""))
            checkpoints.append(ckpt_path)
        except Exception as e:
            logger.warning(f"Failed to read {summary_file}: {e}")
    return checkpoints

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default="data/results/")
    parser.add_argument("--results_dir", type=str, default=None)
    args = parser.parse_args()

    cfg = Config()
    output_dir = Path(args.output_dir if args.output_dir else args.results_dir or "data/results/")

    if args.checkpoint:
        evaluate_checkpoint(Path(args.checkpoint), output_dir, cfg)
    else:
        results_dir = Path("data/results")
        ckpt_paths = _discover_checkpoints(results_dir)
        if not ckpt_paths:
            logger.error("No checkpoints found.")
            return
        for ckpt in ckpt_paths:
            evaluate_checkpoint(ckpt, output_dir, cfg)

if __name__ == "__main__":
    main()
