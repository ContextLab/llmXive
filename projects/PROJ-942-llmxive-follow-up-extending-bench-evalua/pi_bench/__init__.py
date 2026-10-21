"""
pi_bench dataset package.

This package provides a minimal HuggingFace `datasets` loader for the placeholder
π‑Bench dataset downloaded by `code/pipelines/download_pi_bench.py`. It loads all
JSON files found under the supplied `data_dir` (defaulting to `data/raw`) and
returns each file's path and raw JSON content as a string.

The loader is deliberately simple: it does not attempt to parse the internal
structure of the JSON files because downstream pipelines operate on the raw
files directly (e.g., `parse_traces.py`). The primary purpose is to satisfy the
quick‑start command:

    python -c "from datasets import load_dataset; load_dataset('pi_bench', data_dir='data/raw')"

which expects a dataset named `pi_bench` to be importable from the project root.
"""

# The module is intentionally empty; all logic resides in `pi_bench.py`.
