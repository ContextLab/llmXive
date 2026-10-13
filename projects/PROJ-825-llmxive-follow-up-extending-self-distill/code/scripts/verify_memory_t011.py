"""
verify_memory_t011.py

Utility script used by the T011 tests to verify that loading the required models
fits within the 7 GB RAM budget. It provides three public callables:

* ``get_peak_rss_gb`` – returns the current process peak RSS in gigabytes.
* ``load_models_and_measure`` – loads the student model (Qwen2.5‑1.7B, 8‑bit) and
  the dense retriever (sentence‑transformers/all‑MiniLM‑L6‑v2), runs a single
  forward pass on each, and returns the measured peak RSS.
* ``main`` – orchestrates the loading/measurement, writes the result to
  ``data/processed/memory_dry_run.json`` and exits with a non‑zero status code
  if the measured memory exceeds the 7 GB constitutional limit.
"""

import json
import sys
import psutil
from pathlib import Path

from llmxive_toolkit import paths

# --------------------------------------------------------------------------- #
# Helper: peak RSS in gigabytes
# --------------------------------------------------------------------------- #
def get_peak_rss_gb() -> float:
    """
    Return the resident set size (RSS) of the current process in gigabytes.
    """
    process = psutil.Process()
    rss_bytes = process.memory_info().rss
    return rss_bytes / (1024 ** 3)  # GB

# --------------------------------------------------------------------------- #
# Model loading & a single forward pass
# --------------------------------------------------------------------------- #
def load_models_and_measure() -> float:
    """
    Load the required models, perform a minimal forward pass for each, and
    return the peak RSS memory consumption in gigabytes.

    This function deliberately **does not** catch any exceptions – any failure
    (e.g. OOM, missing internet access) should propagate so that the caller
    (or the execution environment) can handle it (e.g. by switching to a GPU
    runner on Kaggle).
    """
    # ------------------------------------------------- #
    # 1. Load the Qwen2.5‑1.7B student model (8‑bit) #
    # ------------------------------------------------- #
    from transformers import AutoModelForCausalLM, AutoTokenizer

    # The model name follows the HuggingFace repository naming convention.
    # ``load_in_8bit=True`` triggers bitsandbytes quantisation.
    student_model_name = "Qwen/Qwen2.5-1.7B"
    tokenizer = AutoTokenizer.from_pretrained(student_model_name, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        student_model_name,
        device_map="auto",
        load_in_8bit=True,
        torch_dtype="auto",
    )
    model.eval()

    # Minimal inference: a single tokenised prompt.
    inputs = tokenizer("Hello world!", return_tensors="pt")
    # Move inputs to the same device as the model.
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        _ = model(**inputs)

    # ------------------------------------------------- #
    # 2. Load the dense retriever (sentence‑transformers) #
    # ------------------------------------------------- #
    from sentence_transformers import SentenceTransformer

    retriever_name = "sentence-transformers/all-MiniLM-L6-v2"
    retriever = SentenceTransformer(retriever_name, device="cpu")
    # Encode a single dummy sentence.
    _ = retriever.encode(["dummy sentence"], show_progress_bar=False)

    # ------------------------------------------------- #
    # 3. Measure peak RSS after both forward passes #
    # ------------------------------------------------- #
    peak_gb = get_peak_rss_gb()
    return peak_gb

# --------------------------------------------------------------------------- #
# Main entry point used by the script and by the test suite
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Execute the dry‑run memory check, write the JSON output and enforce the
    7 GB memory gate.
    """
    peak_gb = load_models_and_measure()

    # Write JSON output – the quickstart expects the file under
    # ``data/processed/memory_dry_run.json``.
    output_path = paths.data("processed", "memory_dry_run.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"peak_rss_mb": round(peak_gb * 1024, 2)}, f, indent=2)

    # Exit with status 1 if the memory consumption exceeds the constitutional
    # limit of 7 GB.
    if peak_gb > 7.0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
