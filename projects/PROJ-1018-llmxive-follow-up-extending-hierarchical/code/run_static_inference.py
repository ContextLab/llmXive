"""
Run a small end‑to‑end static‑index inference pipeline.

This script:
1. Loads the relevance profiles produced by the dynamic extraction step.
2. Builds a static index (PCA + K‑Means) with the configured number of clusters.
3. Saves the static index to ``data/processed/static_index_k{K}.json``.
4. Streams the PG‑19 test split, selects the first document that meets the
   minimum token length (≥ 32 k tokens).
5. Tokenises the document with a lightweight causal LM (GPT‑2) and runs
   ``static_inference`` using the pre‑computed static index.
6. Computes a per‑document log‑perplexity and writes a single result row
   to ``data/results/static_inference_result.json``.

The script is deliberately lightweight so that it can run on the
GitHub‑Actions free‑tier CPU runner while still exercising the full
static‑index path on real data.
"""

import json
import logging
import os

import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

from llmxive_toolkit import paths, get_logger

# Import the pipeline components from the existing code base
from src.config import Config
from src.clustering import generate_static_index, save_static_index
from src.inference import static_inference

log = get_logger(__name__)

def _find_long_document(tokenizer, min_tokens, dataset_iter):
    """
    Iterate over a streaming dataset and return the first document whose
    tokenised length meets ``min_tokens``.
    """
    for doc in dataset_iter:
        text = doc.get("text") or doc.get("content") or doc.get("text")
        if not text:
            continue
        token_ids = tokenizer.encode(text, add_special_tokens=False)
        if len(token_ids) >= min_tokens:
            # Use a stable identifier if the dataset provides one;
            # otherwise fall back to a hash of the text.
            doc_id = doc.get("id") or doc.get("doc_id") or str(hash(text))
            return doc_id, token_ids
    raise RuntimeError(
        f"No document in the streamed dataset contains at least {min_tokens} tokens."
    )

def _compute_log_perplexity(logits: torch.Tensor, input_ids: torch.Tensor) -> float:
    """
    Compute the average log‑perplexity for a single sequence.
    ``logits`` are expected to have shape (batch, seq_len, vocab_size).
    """
    # Shift so that tokens <t> predict token <t+1>
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = input_ids[..., 1:].contiguous()

    loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
    loss = loss_fct(
        shift_logits.view(-1, shift_logits.size(-1)),
        shift_labels.view(-1)
    )
    total_loss = loss.sum().item()
    n_tokens = shift_labels.numel()
    # Negative average log‑likelihood = log‑perplexity
    return - (total_loss / n_tokens)

def main():
    # ------------------------------------------------------------------
    # 1️⃣  Load configuration and relevance profiles
    # ------------------------------------------------------------------
    cfg = Config()
    profiles_path = paths.interim("relevance_profiles.json")
    if not os.path.exists(profiles_path):
        raise FileNotFoundError(f"Relevance profiles not found at {profiles_path}")

    with open(profiles_path, "r") as f:
        relevance_profiles = json.load(f)

    log.info(f"Loaded {len(relevance_profiles)} relevance profiles")

    # ------------------------------------------------------------------
    # 2️⃣  Build and persist the static index
    # ------------------------------------------------------------------
    static_index = generate_static_index(
        profiles=relevance_profiles,
        k=cfg.k_clusters,
        pca_components=64,   # per‑task requirement
        seed=cfg.seed
    )
    static_index_path = paths.processed(f"static_index_k{cfg.k_clusters}.json")
    save_static_index(static_index, static_index_path)
    log.info(f"Static index saved to {static_index_path}")

    # ------------------------------------------------------------------
    # 3️⃣  Load a real ≥ 32k‑token PG‑19 document
    # ------------------------------------------------------------------
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    # Ensure the tokenizer has a BOS token – GPT‑2 does not, so we add one
    if tokenizer.bos_token is None:
        tokenizer.add_special_tokens({"bos_token": "<bos>"})

    dataset = load_dataset(
        "lmsys/pg-19-test",
        split="test",
        streaming=True
    )
    doc_id, token_ids = _find_long_document(
        tokenizer=tokenizer,
        min_tokens=cfg.min_document_tokens,
        dataset_iter=dataset
    )
    log.info(f"Selected document {doc_id} with {len(token_ids)} tokens")

    # Convert to a torch tensor (batch‑size = 1)
    input_ids = torch.tensor([token_ids], dtype=torch.long)

    # ------------------------------------------------------------------
    # 4️⃣  Load a lightweight causal LM and run static inference
    # ------------------------------------------------------------------
    model = AutoModelForCausalLM.from_pretrained("gpt2")
    model.eval()

    inference_output = static_inference(
        model=model,
        static_index=static_index,
        input_ids=input_ids,
        config=cfg
    )
    logits = inference_output["logits"]

    # ------------------------------------------------------------------
    # 5️⃣  Compute log‑perplexity and write the result row
    # ------------------------------------------------------------------
    log_perplexity = _compute_log_perplexity(logits, input_ids)

    result = {
        "document_id": doc_id,
        "log_perplexity": log_perplexity
    }

    result_path = paths.results("static_inference_result.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    log.info(f"Static inference result written to {result_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()