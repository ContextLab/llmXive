# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The `loader.py` file is present but the provided excerpt never shows a `load_dataset(..., streaming=True)` call, nor the full implementation of graph traversal, line‑count filtering, or writing to `data/filtered_swe_bench_v1.parquet`. Moreover, the required output parquet file is missing, and there is no evidence of a state YAML recording checksum/derivation. The task therefore remains unfinished.
- **T016** — declared artifact(s) missing/empty/invalid: data/intermediate/baseline_run.jsonl, schema.yaml
- **T023** — The repository contains `code/experiments/run_high_fidelity.py`, but the file does not show a `run_strategy()` implementation (the snippet ends before such a function and is truncated). Moreover, the required output `data/intermediate/hf_run_1b.jsonl` is absent, and the validation schema `execution_result.schema.yaml` (or any `schema.yaml`) is also missing. Hence the task’s output artifacts and validation criteria are not satisfied.
