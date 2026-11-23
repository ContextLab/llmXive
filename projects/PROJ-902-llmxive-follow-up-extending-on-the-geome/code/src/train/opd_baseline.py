"""
OPD Baseline Training Script
----------------------------
Trains the TinyLlama model for exactly three epochs on the GSM8K dataset,
logs training loss and token‑level accuracy, and persists per‑layer weight
deltas to ``data/baseline_deltas/``.

The script is deliberately lightweight:
* It streams the GSM8K dataset (downloaded by ``src/data/download_gsm8k.py``)
  and uses a small slice (first 200 examples) so that the script finishes
  well within the CI time budget while still operating on **real** data.
* Model loading uses 8‑bit CPU quantisation via ``bitsandbytes`` (if
  available) to keep memory usage low.
* All logging is performed through the project's ``JsonLineLogger`` utility.
* Per‑layer weight deltas are saved as ``torch`` tensors in
  ``data/baseline_deltas/<layer_name>.pt``.
"""

import json
import os
from pathlib import Path
from typing import Dict, List

import torch
from torch import nn
from torch.optim import AdamW
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

from src.utils.random_seed import set_random_seed
from src.utils.logging import JsonLineLogger
from src.utils.resource_monitor import check_resource_limits

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v0.1"
DATA_DIR = Path("data/gsm8k")
DELTAS_DIR = Path("data/baseline_deltas")
LOG_PATH = Path("data/opd_baseline_logs.jsonl")
EPOCHS = 3
BATCH_SIZE = 4  # small batch to stay within RAM limits
MAX_TRAIN_EXAMPLES = 200  # use a real slice of the dataset

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def load_model_and_tokenizer() -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load TinyLlama with 8‑bit CPU quantisation (if ``bitsandbytes`` is
    installed). Falls back to full‑precision if quantisation fails.
    """
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            load_in_8bit=True,
            device_map="auto",
            torch_dtype=torch.float32,
        )
    except Exception as exc:  # pragma: no cover – fallback path
        print(f"8‑bit load failed ({exc}); loading full‑precision model.")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
        )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer

def stream_gsm8k(split: str = "train"):
    """
    Stream the GSM8K split from the local cache directory.
    Returns an iterator of raw examples (dicts with a ``question`` and
    ``answer`` field). The dataset is stored as JSONL files by the
    ``download_gsm8k`` script.
    """
    jsonl_path = DATA_DIR / f"{split}.jsonl"
    if not jsonl_path.is_file():
        raise FileNotFoundError(
            f"GSM8K split file not found at {jsonl_path}. "
            "Run `python -m src.data.download_gsm8k` first."
        )
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def prepare_batch(
    examples: List[Dict[str, str]], tokenizer: AutoTokenizer
) -> dict:
    """
    Convert a list of GSM8K examples into a batch suitable for causal LM
    training. Concatenates ``question`` + ``answer`` with a newline separator.
    """
    texts = [
        f"{ex['question'].strip()}\n{ex['answer'].strip()}" for ex in examples
    ]
    encodings = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    # Labels are the same as input_ids shifted right; transformers handles this
    encodings["labels"] = encodings["input_ids"].clone()
    return encodings

def compute_token_accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """
    Compute token‑level accuracy (ignoring padding tokens).
    """
    predictions = torch.argmax(logits, dim=-1)
    mask = labels != -100  # transformers uses -100 for ignored positions
    correct = (predictions == labels) & mask
    total = mask.sum().item()
    if total == 0:
        return 0.0
    return correct.sum().item() / total

def save_weight_deltas(
    initial_state: Dict[str, torch.Tensor],
    trained_state: Dict[str, torch.Tensor],
    out_dir: Path,
) -> None:
    """
    Compute per‑layer weight deltas and persist each as ``<layer_name>.pt``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, param in trained_state.items():
        if name not in initial_state:
            continue
        delta = param.cpu() - initial_state[name].cpu()
        delta_path = out_dir / f"{name.replace('.', '_')}.pt"
        torch.save(delta, delta_path)

# --------------------------------------------------------------------------- #
# Main training routine
# --------------------------------------------------------------------------- #
def main() -> None:
    # --------------------------------------------------- #
    # 1️⃣  Seed everything for reproducibility
    # --------------------------------------------------- #
    set_random_seed(42)  # project‑wide deterministic seed
    set_seed(42)  # transformers' internal seed helper

    # --------------------------------------------------- #
    # 2️⃣  Initialise logger
    # --------------------------------------------------- #
    logger = JsonLineLogger(LOG_PATH)

    # --------------------------------------------------- #
    # 3️⃣  Load model, tokenizer and capture initial weights
    # --------------------------------------------------- #
    model, tokenizer = load_model_and_tokenizer()
    model.train()
    device = torch.device("cpu")
    model.to(device)

    # Store a copy of the initial parameters (CPU tensors)
    initial_state = {
        name: param.clone().cpu() for name, param in model.named_parameters()
    }

    optimizer = AdamW(model.parameters(), lr=5e-5)

    # --------------------------------------------------- #
    # 4️⃣  Prepare training data (real GSM8K examples)
    # --------------------------------------------------- #
    dataset_iter = stream_gsm8k("train")
    # Take a deterministic slice of the first N examples
    examples = []
    for ex in dataset_iter:
        examples.append(ex)
        if len(examples) >= MAX_TRAIN_EXAMPLES:
            break

    # --------------------------------------------------- #
    # 5️⃣  Training loop (exactly three epochs)
    # --------------------------------------------------- #
    total_steps = (len(examples) // BATCH_SIZE) * EPOCHS
    step = 0
    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0.0
        epoch_acc = 0.0
        batches = [
            examples[i : i + BATCH_SIZE]
            for i in range(0, len(examples), BATCH_SIZE)
        ]

        for batch_examples in batches:
            batch = prepare_batch(batch_examples, tokenizer)
            batch = {k: v.to(device) for k, v in batch.items()}

            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()

            # Compute accuracy for this batch
            with torch.no_grad():
                acc = compute_token_accuracy(
                    outputs.logits.detach(), batch["labels"]
                )

            epoch_loss += loss.item()
            epoch_acc += acc
            step += 1

        avg_loss = epoch_loss / len(batches)
        avg_acc = epoch_acc / len(batches)

        # --------------------------------------------------- #
        # 6️⃣  Log epoch metrics
        # --------------------------------------------------- #
        logger.log(
            {
                "epoch": epoch,
                "average_loss": avg_loss,
                "average_token_accuracy": avg_acc,
                "step": step,
                "total_steps": total_steps,
            }
        )
        print(
            f"[Epoch {epoch}] loss={avg_loss:.4f}  token_acc={avg_acc:.4f}"
        )

    # --------------------------------------------------- #
    # 7️⃣  Persist per‑layer weight deltas
    # --------------------------------------------------- #
    trained_state = {
        name: param.clone().cpu() for name, param in model.named_parameters()
    }
    save_weight_deltas(initial_state, trained_state, DELTAS_DIR)

    # --------------------------------------------------- #
    # 8️⃣  Resource limit validation (project contract)
    # --------------------------------------------------- #
    check_resource_limits()  # raises if RAM > 7 GB or wall‑clock > 360 min

    print(f"Training complete. Weight deltas saved to {DELTAS_DIR}")

if __name__ == "__main__":
    main()
